package org.hackintosh1980.blebridge;

import android.bluetooth.*;
import android.bluetooth.le.*;
import android.content.Context;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.text.SimpleDateFormat;
import java.util.*;

public class BleBridgePersistent {

    private static final String TAG = "BleGattBridge";
    private static final long WRITE_INTERVAL_MS = 1200L;

    // ThermoPro TP351S
    private static final UUID TP_SERVICE =
            UUID.fromString("00010203-0405-0607-0809-0a0b0c0d1910");
    private static final UUID TP_CHAR =
            UUID.fromString("00010203-0405-0607-0809-0a0b0c0d2b10");

    private static volatile boolean running = false;

    private static BluetoothGatt gatt;
    private static BluetoothDevice device;

    private static File outFile;
    private static final Object lock = new Object();
    private static JSONObject lastPacket = null;

    private static String ts() {
        return new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ",
                Locale.US).format(new Date());
    }

    // -------------------------------------------------------------------
    // START
    // -------------------------------------------------------------------
    public static String start(Context ctx, String outName) {
        if (running) return "ALREADY";
        running = true;

        outFile = new File(ctx.getFilesDir(), outName);

        BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
        if (adapter == null || !adapter.isEnabled()) return "BT_OFF";

        BluetoothLeScanner scanner = adapter.getBluetoothLeScanner();
        if (scanner == null) return "NO_SCANNER";

        Log.i(TAG, "Scanning for ThermoPro TP351S…");

        // Scan callback ---------------------------------------------------
        ScanCallback scanCb = new ScanCallback() {
            @Override
            public void onScanResult(int callbackType, ScanResult r) {
                BluetoothDevice d = r.getDevice();
                if (d == null || d.getName() == null) return;

                if (d.getName().contains("TP351") || d.getName().contains("Thermo")) {
                    Log.i(TAG, "Found ThermoPro: " + d.getName());
                    scanner.stopScan(this);
                    device = d;
                    gatt = d.connectGatt(ctx, false, gattCallback);
                }
            }
        };

        scanner.startScan(scanCb);

        // Writer thread ---------------------------------------------------
        new Thread(() -> {
            while (running) {
                try {
                    JSONObject e;
                    synchronized (lock) { e = lastPacket; }
                    JSONArray arr = new JSONArray();
                    if (e != null) arr.put(e);

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
        }, "GattWriter").start();

        return "OK";
    }

    // -------------------------------------------------------------------
    // STOP
    // -------------------------------------------------------------------
    public static void stop() {
        running = false;
        if (gatt != null) {
            gatt.close();
            gatt = null;
        }
        Log.i(TAG, "GATT stopped");
    }

    // -------------------------------------------------------------------
    // GATT CALLBACK
    // -------------------------------------------------------------------
    private static final BluetoothGattCallback gattCallback =
            new BluetoothGattCallback() {

        @Override
        public void onConnectionStateChange(BluetoothGatt g, int status, int newState) {
            if (newState == BluetoothProfile.STATE_CONNECTED) {
                Log.i(TAG, "Connected → discover services");
                g.discoverServices();
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                Log.i(TAG, "Disconnected");
            }
        }

        @Override
        public void onServicesDiscovered(BluetoothGatt g, int status) {
            BluetoothGattService s = g.getService(TP_SERVICE);
            if (s == null) {
                Log.e(TAG, "ThermoPro service not found");
                return;
            }

            BluetoothGattCharacteristic c = s.getCharacteristic(TP_CHAR);
            if (c == null) {
                Log.e(TAG, "ThermoPro characteristic not found");
                return;
            }

            g.setCharacteristicNotification(c, true);

            BluetoothGattDescriptor d = c.getDescriptor(
                    UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"));
            if (d != null) {
                d.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE);
                g.writeDescriptor(d);
            }
        }

        @Override
        public void onCharacteristicChanged(BluetoothGatt g,
                                            BluetoothGattCharacteristic ch) {
            byte[] v = ch.getValue();
            if (v == null) return;
            StringBuilder sb = new StringBuilder();
            for (byte b : v) sb.append(String.format("%02X", b));

            JSONObject obj = new JSONObject();
            try {
                obj.put("timestamp", ts());
                obj.put("name", device != null ? device.getName() : "ThermoPro");
                obj.put("address", device != null ? device.getAddress() : "?");
                obj.put("rssi", 0);
                obj.put("raw", sb.toString());
                obj.put("note", "gatt");
            } catch (Exception ignored) {}

            synchronized (lock) { lastPacket = obj; }
        }
    };
}
