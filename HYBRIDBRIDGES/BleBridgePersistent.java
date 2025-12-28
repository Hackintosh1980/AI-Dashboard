package org.hackintosh1980.blebridge;

import android.bluetooth.*;
import android.bluetooth.le.*;
import android.content.Context;
import android.util.Log;
import android.util.SparseArray;
import org.json.*;

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;

public class BleBridgePersistent {
    private static final String TAG = "BleBridgePersistent";
    private static final int COMPANY_ID = 0x0019;
    private static final long WRITE_INTERVAL_MS = 1500L;

    private static volatile boolean running = false;
    private static BluetoothLeScanner scanner;
    private static ScanCallback callback;
    private static File outFile;
    private static final Object lock = new Object();
    private static final Map<String, JSONObject> last = new HashMap<>();

    private static String ts() {
        return new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ", Locale.US)
                .format(new Date());
    }

    public static String start(Context ctx, String outName) {
        try {
            if (running) return "ALREADY";
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null || !adapter.isEnabled()) return "BT_OFF";

            scanner = adapter.getBluetoothLeScanner();
            if (scanner == null) return "NO_SCANNER";

            outFile = new File(ctx.getFilesDir(), outName);
            Log.i(TAG, "→ writing to " + outFile.getAbsolutePath());
            running = true;

            callback = new ScanCallback() {
                @Override
                public void onScanResult(int type, ScanResult r) {
                    try {
                        BluetoothDevice d = r.getDevice();
                        if (d == null) return;
                        ScanRecord rec = r.getScanRecord();
                        if (rec == null) return;

                        SparseArray<byte[]> md = rec.getManufacturerSpecificData();
                        if (md == null || md.size() == 0) return;
                        byte[] payload = md.get(COMPANY_ID);
                        if (payload == null && md.size() > 0)
                            payload = md.valueAt(0);

                        StringBuilder sb = new StringBuilder();
                        if (payload != null)
                            for (byte b : payload)
                                sb.append(String.format("%02X", b));

                        JSONObject obj = new JSONObject();
                        obj.put("timestamp", ts());
                        obj.put("name", d.getName() != null ? d.getName() : "(unknown)");
                        obj.put("address", d.getAddress());
                        obj.put("rssi", r.getRssi());
                        obj.put("raw", sb.toString());
                        obj.put("note", "android raw dump");

                        synchronized (lock) { last.put(d.getAddress(), obj); }
                    } catch (Throwable t) {
                        Log.e(TAG, "scan", t);
                    }
                }
            };

            scanner.startScan(callback);

            new Thread(() -> {
                while (running) {
                    try {
                        JSONArray arr;
                        synchronized (lock) { arr = new JSONArray(last.values()); }
                        File tmp = new File(outFile.getAbsolutePath() + ".tmp");
                        try (FileOutputStream fos = new FileOutputStream(tmp, false)) {
                            fos.write(arr.toString(2).getBytes());
                        }
                        tmp.renameTo(outFile);
                        Thread.sleep(WRITE_INTERVAL_MS);
                    } catch (Throwable t) {
                        Log.e(TAG, "writer", t);
                    }
                }
            }, "Writer").start();

            return "OK";
        } catch (Throwable t) {
            Log.e(TAG, "start", t);
            return "ERR:" + t.getMessage();
        }
    }

    public static void stop() {
        try {
            running = false;
            if (scanner != null && callback != null)
                scanner.stopScan(callback);
            Log.i(TAG, "stopped");
        } catch (Throwable t) {
            Log.e(TAG, "stop", t);
        }
    }
}
