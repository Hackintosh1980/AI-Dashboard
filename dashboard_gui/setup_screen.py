# setup_screen.py – Session42 FIXED CLEAN (REPAIRED)

import os
import json
import time

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.utils import platform

from dashboard_gui.ui.setup_content.setup_main_panel import SetupMainPanel
from dashboard_gui.ui.common.header_online import HeaderBar
import config


_selected = {}      # mac -> { "adv": str, "gatt": str, "bridge": str }
_device_names = {}  # mac -> display name   ✅ FEHLTE


def _raw_path():
    return os.path.join(config.DATA, "ble_dump.json")



class SetupScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)

        # -------------------------------------------
        # Registrierung beim Global State Manager
        # -------------------------------------------
        from dashboard_gui.global_state_manager import GLOBAL_STATE
        GLOBAL_STATE.attach_setup(self)

        root = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.add_widget(root)

        self.header = HeaderBar(
            goto_setup=lambda *_: None,
            goto_debug=lambda *_: setattr(self.manager, "current", "debug"),
            goto_device_picker=lambda *_: setattr(self.manager, "current", "device_picker"),
        )
        self.header.lbl_title.text = "Setup"
        self.header.update_back_button("setup")
        root.add_widget(self.header)

        self.panel = SetupMainPanel(
            on_refresh=self.update_devices,
            on_save=self._save,
            on_back=self._back,
            on_profile_change=self._set_profile,
            on_adv=self.set_adv,
            on_gatt=self.set_gatt,
            on_bridge=self.set_bridge,
            on_restart_bridge=self._restart_bridge,
            on_restart_adv=self._restart_adv,
            on_restart_gatt=self._restart_gatt,
        )
        root.add_widget(self.panel)

        Clock.schedule_once(self.update_devices, 0.3)

    def _restart_adv(self, *_):
        try:
            import core
            core.restart_adv_bridge()
            print("[Setup] ADV Bridge neu gestartet")
        except Exception as e:
            print("[Setup] ADV restart FEHLER:", e)
    
    def _restart_gatt(self, *_):
        try:
            import core
            core.restart_gatt_bridge()
            print("[Setup] GATT Bridge neu gestartet")
        except Exception as e:
            print("[Setup] GATT restart FEHLER:", e)


    # ---------------------------------------------------------
    def _restart_bridge(self, *_):
        try:
            import core
            core.stop()
            core.start()
            print("[Setup] Bridge manuell neu gestartet")
        except Exception as e:
            print("[Setup] Bridge restart FEHLER:", e)

    # ---------------------------------------------------------
    def update_devices(self, *_):
        self.panel.clear_devices()
    
        path = _raw_path()
        if not os.path.exists(path):
            print("[Setup] dump fehlt")
            return
    
        try:
            with open(path, "r", encoding="utf-8") as f:
                arr = json.load(f)
        except Exception:
            print("[Setup] JSON Fehler")
            return
    
        for e in arr:
            mac = e.get("address")
            raw = e.get("adv_raw") or e.get("gat_raw") or e.get("log_raw")
            name = e.get("name") or mac
    
            if not mac or not raw:
                continue
    
            _device_names[mac] = name
            sel = _selected.get(mac, {})
    
            adv = sel.get("adv", config.get_adv_decoder(mac))
            gatt = sel.get("gatt", config.get_gatt_decoder(mac))
            bridge = sel.get("bridge", config.get_bridge_profile(mac))
    
            # 🔥 KEIN STATUS MEHR
            self.panel.add_device(
                name=name,
                adv=adv,
                gatt=gatt,
                bridge=bridge,
                mac=mac
            )


    # ---------------------------------------------------------
    def _set_profile(self, mac, prof):
        _selected[mac] = {"profile": prof}

    # ---------------------------------------------------------
    def _save(self, *_):
        cfg = config._init()
    
        devices = {}
    
        for mac, sel in _selected.items():
            # nur speichern, wenn IRGENDEINE Auswahl existiert
            if not sel:
                continue
    
            name = _device_names.get(mac, mac)
    
            devices[mac] = {
                "name": name,
                "adv_decoder": sel.get("adv", ""),
                "gatt_decoder": sel.get("gatt", ""),
                "bridge_profile": sel.get("bridge", "")
            }
    
        cfg["devices"] = devices
    
        config.save(cfg)
        config.reload()
    
        print("[Setup] config gespeichert (nur explizit gewählte Devices)")


    # ---------------------------------------------------------
    def _back(self, *_):
        if self.manager:
            self.manager.current = "dashboard"

    def set_adv(self, mac, val):
        if val == "---":
            _selected.setdefault(mac, {}).pop("adv", None)
        else:
            _selected.setdefault(mac, {})["adv"] = val

    def set_gatt(self, mac, val):
        if val == "---":
            _selected.setdefault(mac, {}).pop("gatt", None)
        else:
            _selected.setdefault(mac, {})["gatt"] = val

    def set_bridge(self, mac, val):
        if val == "---":
            _selected.setdefault(mac, {}).pop("bridge", None)
        else:
            _selected.setdefault(mac, {})["bridge"] = val

    # ---------------------------------------------------------
    # LIVE UPDATE FROM GSM (nur Header)
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # LIVE UPDATE FROM GSM (nur Header)
    # ---------------------------------------------------------
    def update_from_global(self, d):
        self.header.update_from_global(d)
