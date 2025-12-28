package org.hackintosh1980.blebridge;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothGattService;
import android.bluetooth.BluetoothLeScanner;
import android.bluetooth.BluetoothProfile;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanRecord;
import android.bluetooth.le.ScanResult;
import android.content.Context;
import android.util.Log;
import android.util.SparseArray;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

public class BleBridgePersistent {

    private static final String TAG = "BleHybridBridge";

    // Schreibintervall für ble_dump.json
    private static final long WRITE_INTERVAL_MS = 1200L;

    // Manufacturer-ID (wie bei deiner alten Scan-Bridge)
    private static final int COMPANY_ID = 0x0019;

    // ThermoPro TP351S GATT-Service/Char (wie Desktop-GATT)
    private static final UUID TP_SERVICE =
            UUID.fromString("00010203-0405-0607-0809-0a0b0c0d1910");
    private static final UUID TP_CHAR =
            UUID.fromString("00010203-0405-0607-0809-0a0b0c0d2b10");

    private static volatile boolean running = false;

    private static BluetoothLeScanner scanner;
    private static ScanCallback scanCb;

    private static BluetoothGatt gatt;
    private static BluetoothDevice tpDevice;

    private static File outFile;
    private static final Object lock = new Object();
    private static final Map<String, JSONObject> last = new HashMap<>();

    // Zähler für pseudo-Manufacturer aus GATT
    private static int gattCounter = 0;

    private static String ts() {
        return new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ",
                Locale.US).format(new Date());
    }

    private static String bytesToHex(byte[] data) {
        if (data == null) return "";
        StringBuilder sb = new StringBuilder(data.length * 2);
        for (byte b : data) {
            sb.append(String.format(Locale.US, "%02X", b));
        }
        return sb.toString();
    }

    // ------------------------------------------------------------
    // START – wird von Python via pyjnius aufgerufen
    // ------------------------------------------------------------
    public static String start(Context ctx, String outName) {
        if (running) {
            return "ALREADY";
        }

        BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
        if (adapter == null || !adapter.isEnabled()) {
            return "BT_OFF";
        }

        scanner = adapter.getBluetoothLeScanner();
        if (scanner == null) {
            return "NO_SCANNER";
        }

        outFile = new File(ctx.getFilesDir(), outName);
        running = true;
        gattCounter = 0;
        tpDevice = null;
        gatt = null;

        Log.i(TAG, "Hybrid-Bridge START → " + outFile.getAbsolutePath());

        // Gemeinsamer Scan-Callback: Manufacturer + GATT-Trigger
        scanCb = new ScanCallback() {
            @Override
            public void onScanResult(int callbackType, ScanResult r) {
                try {
                    BluetoothDevice d = r.getDevice();
                    if (d == null) return;

                    ScanRecord rec = r.getScanRecord();
                    int rssi = r.getRssi();
                    String addr = d.getAddress();
                    String name = (d.getName() != null) ? d.getName() : "(unknown)";

                    // 1) Manufacturer-Daten wie alte Bridge
                    if (rec != null) {
                        SparseArray<byte[]> md = rec.getManufacturerSpecificData();
                        if (md != null && md.size() > 0) {
                            byte[] payload = md.get(COMPANY_ID);
                            if (payload == null) {
                                // Wenn anderer Hersteller, dann nimm ersten Eintrag
                                payload = md.valueAt(0);
                            }

                            if (payload != null && payload.length > 0) {
                                String rawHex = bytesToHex(payload);

                                JSONObject obj = new JSONObject();
                                obj.put("timestamp", ts());
                                obj.put("name", name);
                                obj.put("address", addr);
                                obj.put("rssi", rssi);
                                obj.put("raw", rawHex);
                                obj.put("note", "adv");

                                synchronized (lock) {
                                    last.put(addr, obj);
                                }
                            }
                        }
                    }

                    // 2) GATT-Trigger für ThermoPro TP351S (nur 1x connect)
                    if (tpDevice == null && name != null) {
                        if (name.contains("TP351") || name.contains("Thermo")) {
                            Log.i(TAG, "Found ThermoPro for GATT: " + name);
                            tpDevice = d;
                            // Scanner kann weiterlaufen – wir stoppen hier NICHT,
                            // damit Manufacturer weiterläuft.
                            gatt = d.connectGatt(ctx, false, gattCallback);
                        }
                    }
                } catch (Throwable t) {
                    Log.e(TAG, "scan", t);
                }
            }
        };

        scanner.startScan(scanCb);

        // Writer-Thread für ble_dump.json
        new Thread(new Runnable() {
            @Override
            public void run() {
                while (running) {
                    try {
                        JSONArray arr = new JSONArray();
                        synchronized (lock) {
                            for (JSONObject o : last.values()) {
                                arr.put(o);
                            }
                        }

                        File tmp = new File(outFile.getAbsolutePath() + ".tmp");
                        FileOutputStream fos = new FileOutputStream(tmp, false);
                        fos.write(arr.toString(2).getBytes());
                        fos.close();
                        // atomarer Swap
                        tmp.renameTo(outFile);

                        Thread.sleep(WRITE_INTERVAL_MS);
                    } catch (Throwable t) {
                        Log.e(TAG, "writer", t);
                    }
                }
                Log.i(TAG, "Writer-Thread beendet");
            }
        }, "HybridWriter").start();

        return "OK";
    }

    // ------------------------------------------------------------
    // STOP – wird von Python Core aufgerufen
    // ------------------------------------------------------------
    public static void stop() {
        running = false;

        try {
            if (scanner != null && scanCb != null) {
                scanner.stopScan(scanCb);
            }
        } catch (Throwable t) {
            Log.e(TAG, "stop scan", t);
        }

        try {
            if (gatt != null) {
                gatt.close();
            }
        } catch (Throwable t) {
            Log.e(TAG, "stop gatt", t);
        }

        scanner = null;
        scanCb = null;
        gatt = null;
        tpDevice = null;

        Log.i(TAG, "Hybrid-Bridge STOP");
    }

    // ------------------------------------------------------------
    // GATT Callback – macht aus Notifications pseudo-Manufacturer
    // ------------------------------------------------------------
    private static final BluetoothGattCallback gattCallback =
            new BluetoothGattCallback() {

        @Override
        public void onConnectionStateChange(BluetoothGatt g, int status, int newState) {
            if (newState == BluetoothProfile.STATE_CONNECTED) {
                Log.i(TAG, "GATT connected → discover services");
                g.discoverServices();
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                Log.i(TAG, "GATT disconnected");
            }
        }

        @Override
        public void onServicesDiscovered(BluetoothGatt g, int status) {
            try {
                BluetoothGattService s = g.getService(TP_SERVICE);
                if (s == null) {
                    Log.e(TAG, "ThermoPro TP_SERVICE not found");
                    return;
                }

                BluetoothGattCharacteristic c = s.getCharacteristic(TP_CHAR);
                if (c == null) {
                    Log.e(TAG, "ThermoPro TP_CHAR not found");
                    return;
                }

                g.setCharacteristicNotification(c, true);

                BluetoothGattDescriptor d = c.getDescriptor(
                        UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"));
                if (d != null) {
                    d.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE);
                    g.writeDescriptor(d);
                }

                Log.i(TAG, "GATT notifications enabled");
            } catch (Throwable t) {
                Log.e(TAG, "onServicesDiscovered", t);
            }
        }

        @Override
        public void onCharacteristicChanged(BluetoothGatt g,
                                            BluetoothGattCharacteristic ch) {
            try {
                byte[] v = ch.getValue();
                if (v == null || v.length == 0) return;

                String gattHex = bytesToHex(v);

                // Paket-Zähler für Watchdog / "Living Sensor"
                synchronized (lock) {
                    gattCounter = (gattCounter + 1) & 0xFFFF;
                }
                String cntHex = String.format(Locale.US, "%04X", gattCounter);

                // Pseudo-Manufacturer: [2-Byte Counter] + [GATT Hex Payload]
                String pseudoRaw = cntHex + gattHex;

                String name = (tpDevice != null && tpDevice.getName() != null)
                        ? tpDevice.getName() : "ThermoPro";
                String addr = (tpDevice != null) ? tpDevice.getAddress() : "GATT";

                JSONObject obj = new JSONObject();
                obj.put("timestamp", ts());
                obj.put("name", name);
                obj.put("address", addr);
                obj.put("rssi", 0);                     // per GATT keine RSSI
                obj.put("raw", pseudoRaw);              // das liest dein Decoder
                obj.put("note", "gatt_pseudo");
                obj.put("gatt_raw", gattHex);           // optional für Debug
                obj.put("counter", gattCounter);        // optional

                synchronized (lock) {
                    last.put(addr, obj);
                }

                Log.i(TAG, "GATT packet → pseudo RAW = " + pseudoRaw);
            } catch (Throwable t) {
                Log.e(TAG, "onCharacteristicChanged", t);
            }
        }
    };
}
