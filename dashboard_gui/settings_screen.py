from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from dashboard_gui.global_state_manager import GLOBAL_STATE
from dashboard_gui.ui.common.header_online import HeaderBar
from dashboard_gui.ui.settings_content.settings_main_panel import SettingsMainPanel
import time
import config


class SettingsScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)

        root = BoxLayout(orientation="vertical")

        GLOBAL_STATE.attach_settings(self)

        self.header = HeaderBar(
            goto_setup=lambda *_: setattr(self.manager, "current", "setup"),
            goto_debug=lambda *_: setattr(self.manager, "current", "debug"),
            goto_device_picker=lambda *_: setattr(self.manager, "current", "device_picker")
        )
        self.header.update_back_button("settings")
        root.add_widget(self.header)
        
        

        panel = SettingsMainPanel(
            on_save=self._save,
            on_cancel=self._cancel
        )
        root.add_widget(panel)

        self.add_widget(root)

    # ---------------------------------------------------------
    def _save(self, values: dict):
    
        cfg = config._init()
    
        cfg["refresh_interval"] = float(values["refresh_interval"])
        cfg["ui_refresh_interval"] = float(values["ui_refresh_interval"])
        cfg["stale_timeout"] = float(values["stale_timeout"])
    
        cfg["temperature_offset"] = float(values["temperature_offset"])
        cfg["humidity_offset"] = float(values["humidity_offset"])
        cfg["leaf_offset"] = float(values["leaf_offset"])
    
        cfg["temperature_unit"] = values["temperature_unit"]
    
        # KORREKTER SAVE CALL FÜR SESSION40
        config.save(cfg)
        config.reload()
    
        # ---------------------------------------------------------
        # 🟩 WATCHDOG: RICHTIGE LIVE-AKTUALISIERUNG
        # ---------------------------------------------------------
        try:
            from core import _watchdog
            if _watchdog:
                _watchdog.set_timeout(cfg["stale_timeout"])
                print(f"[SETTINGS] Watchdog stale_timeout live gesetzt → {cfg['stale_timeout']}")
        except Exception as e:
            print("[SETTINGS] Fehler beim Setzen des Watchdog-Timeouts:", e)
        # ---------------------------------------------------------
    
        self.manager.current = "dashboard"
    # ---------------------------------------------------------
    def _cancel(self, *_):
        self.manager.current = "dashboard"
    def update_from_global(self, d):
        self.header.update_from_global(d)