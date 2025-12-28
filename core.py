# core.py – FINAL (stabil)
# © 2025 Dominik Rosenthal

import os
from kivy.utils import platform as kivy_platform

import config
from bridge_manager import get_bridge
from watchdog_manager import DumpWatchdog
from decoder import start_decoder_thread, update_bridge_state

# ------------------------------------------------------------
# 🔥 100 % zuverlässige Android-Erkennung
# ------------------------------------------------------------
def is_android():
    if "ANDROID_ROOT" in os.environ:
        return True
    return kivy_platform == "android"


# globale Instanzen
_bridge = None
_watchdog = None


# ------------------------------------------------------------
# Watchdog Callback
# ------------------------------------------------------------
def _wd_callback(status):
    print(f"[Core] Watchdog: {status['status']} | alive={status['alive']} | last_seen={status['last_seen']}")

    update_bridge_state(
        alive=status["alive"],
        status=status["status"],
        last_seen=status["last_seen"]
    )
# ------------------------------------------------------------
# decoded.json löschen
# ------------------------------------------------------------
def _cleanup_decoded():
    try:
        path = os.path.join(config.DATA, "decoded.json")
        if os.path.exists(path):
            os.remove(path)
            print("[Core] decoded.json entfernt")
    except:
        pass



def _cleanup_ble_dump():
    try:
        import json
        path = os.path.join(config.DATA, "ble_dump.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)

        print(f"[Core] ble_dump.json geleert: {path}")

    except Exception as e:
        print("[Core] ble_dump cleanup failed:", e)
# ------------------------------------------------------------
# START – von main.py
# ------------------------------------------------------------
def start():
    global _bridge, _watchdog

    print("[Core] Starte Core…")
    print("[Core] is_android():", is_android())

    _cleanup_decoded()
    _cleanup_ble_dump()
    # -----------------------------------------------------
    # Bridge starten
    # -----------------------------------------------------
    if is_android():
        try:
            from permission_fix import check_permissions
            check_permissions()
        except:
            print("[Core] Permission check skipped")

        _bridge = get_bridge(prefer_mock=False)
        _bridge.start()
        print("[Core] Android-Bridge gestartet")

    else:
        print("[Core] Desktop Mode – externe blebridge_desktop benutzen")
        _bridge = None

    # -----------------------------------------------------
    # Decoder starten (liefert decoded.json)
    # -----------------------------------------------------
    start_decoder_thread(config.get_refresh_interval())
    print("[Core] Decoder-Thread gestartet")

    # -----------------------------------------------------
    # Watchdog starten
    # -----------------------------------------------------
    _watchdog = DumpWatchdog(
        timeout=config.get_stale_timeout(),
        interval=config.get_refresh_interval(),
        callback=_wd_callback
    )
    _watchdog.start()
    print("[Core] Watchdog gestartet")

    print("[Core] System läuft.")

# ------------------------------------------------------------
# BRIDGE ONLY CONTROL
# ------------------------------------------------------------
def restart_bridge():
    from kivy.clock import Clock

    if not is_android():
        return

    # BLE-Operationen verzögert & im Mainloop
    Clock.schedule_once(_restart_bridge_safe, 0)

def _restart_bridge_safe(dt):
    global _bridge

    try:
        if _bridge:
            _bridge.stop()
            print("[Core] Bridge gestoppt (safe)")
    except Exception as e:
        print("[Core] Bridge stop failed:", e)

    try:
        _bridge = get_bridge(prefer_mock=False)
        _bridge.start()
        print("[Core] Bridge neu gestartet (safe)")
    except Exception as e:
        print("[Core] Bridge start failed:", e)



# ------------------------------------------------------------
# STOP
# ------------------------------------------------------------
def stop():
    global _bridge, _watchdog

    print("[Core] Stoppe System…")

    try:
        if _watchdog:
            _watchdog.stop()
            print("[Core] Watchdog gestoppt")
    except:
        pass

    try:
        if is_android() and _bridge:
            _bridge.stop()
            print("[Core] Bridge gestoppt")
    except:
        pass

    print("[Core] Shutdown abgeschlossen.")
