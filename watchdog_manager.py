import os
import time
import json
import config

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
RAW_PATH = os.path.join(DATA, "ble_dump.json")


class DumpWatchdog:
    CHANNELS = ["adv", "gat", "log"]

    SIGNAL_FIELD = {
        "adv": "adv_raw",
        "gat": "packet_counter",
        "log": "log_raw",
    }

    def __init__(self, timeout, interval, callback):
        self.timeout = float(timeout)
        self.interval = float(interval)
        self.callback = callback
        self._moved = {}  # mac -> {channel: bool}
        self._last_signal = {}   # mac -> {channel: value}
        self._last_ts = {}       # mac -> {channel: ts}

        self.running = False

    def _load(self):
        if not os.path.exists(RAW_PATH):
            return None
        try:
            with open(RAW_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, list) else None
        except Exception:
            return None

    def _find(self, dump, mac):
        for e in dump:
            if isinstance(e, dict) and e.get("address") == mac:
                return e
        return None

    # --------------------------------------------------------
    # EINHEITLICHE KANAL-LOGIK: Bewegung = Leben
    # --------------------------------------------------------
    def _check_channel(self, mac, channel, entry, now):
        field = self.SIGNAL_FIELD[channel]
        signal = entry.get(field) if entry else None

        if signal is None:
            return {"alive": False, "last_seen": None, "status": "OFFLINE"}

        if mac not in self._last_signal:
            self._last_signal[mac] = {}
            self._last_ts[mac] = {}
            self._moved[mac] = {}
        
        last_signal = self._last_signal[mac].get(channel)
        last_ts = self._last_ts[mac].get(channel)
        moved = self._moved[mac].get(channel, False)
        
        # Initial: merken, aber NICHT alive
        if last_signal is None:
            self._last_signal[mac][channel] = signal
            self._last_ts[mac][channel] = now
            self._moved[mac][channel] = False
            return {"alive": False, "last_seen": None, "status": "INIT"}
        
        # Bewegung => alive
        if signal != last_signal:
            self._last_signal[mac][channel] = signal
            self._last_ts[mac][channel] = now
            self._moved[mac][channel] = True
            return {"alive": True, "last_seen": 0.0, "status": "OK"}
        
        # KEINE Bewegung und noch nie bewegt => bleibt tot (kein Timeout-Grace!)
        if not moved:
            return {"alive": False, "last_seen": None, "status": "INIT"}
        # Keine Bewegung → Zeit prüfen
        delta = now - (last_ts or now)

        if delta < self.timeout:
            return {"alive": True, "last_seen": delta, "status": "OK"}

        return {"alive": False, "last_seen": delta, "status": "STALE"}

    # --------------------------------------------------------
    def check_status(self):
        now = time.time()

        try:
            devices = config.get_devices()
        except AttributeError:
            devices = []

        if not devices:
            return {"alive": False, "status": "OFFLINE", "devices": {}}

        dump = self._load()
        if not dump:
            return {"alive": False, "status": "OFFLINE", "devices": {}}

        per_dev = {}
        any_ok = False
        any_stale = False
        max_delta = 0.0

        for mac in devices:
            entry = self._find(dump, mac)
            dev_result = {}

            for channel in self.CHANNELS:
                ch = self._check_channel(mac, channel, entry, now)
                dev_result[channel] = ch

                if ch["status"] == "OK":
                    any_ok = True
                elif ch["status"] == "STALE":
                    any_stale = True
                    if ch["last_seen"] and ch["last_seen"] > max_delta:
                        max_delta = ch["last_seen"]

            per_dev[mac] = dev_result

        if any_ok:
            return {"alive": True, "status": "OK", "last_seen": 0.0, "devices": per_dev}
        if any_stale:
            return {"alive": False, "status": "STALE", "last_seen": max_delta, "devices": per_dev}

        return {"alive": False, "status": "OFFLINE", "last_seen": None, "devices": per_dev}
    # --------------------------------------------------------
    def start(self):
        import threading

        if self.running:
            return
        self.running = True

        def loop():
            while self.running:
                try:
                    self.callback(self.check_status())
                except Exception:
                    pass
                time.sleep(self.interval)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
