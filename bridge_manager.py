#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bridge_manager.py – Plattformübergreifende Bridge-Steuerung 🌿
Android: AdvBridge + GattBridge
Desktop: Dummy
© 2025 Dominik Rosenthal (Hackintosh1980)
"""

from kivy.utils import platform
import os
import config


# ------------------------------------------------------------
# 🧩 Bridge-Basisinterface
# ------------------------------------------------------------
class BridgeInterface:
    def start(self): ...
    def stop(self): ...
    def get_status(self):
        return {
            "running": False,
            "bt_enabled": False,
            "source": "unknown"
        }


# ------------------------------------------------------------
# 🤖 Android-Implementierung (ADV + GATT getrennt)
# ------------------------------------------------------------
class BleBridgeAndroid(BridgeInterface):
    def __init__(self):
        self.running = False
        self.bt_enabled = False

    def start(self):
        try:
            from jnius import autoclass
            import os
            import config
    
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            ctx = PythonActivity.mActivity
    
            AdvBridge = autoclass("org.hackintosh1980.blebridge.AdvBridge")
            GattBridge = autoclass("org.hackintosh1980.blebridge.GattBridge")
    
            gatt_cfg = os.path.join(config.DATA, "gatt_config.json")
    
            ret_adv = AdvBridge.start(ctx)
            ret_gatt = GattBridge.start(ctx, gatt_cfg)
    
            print("[BridgeAndroid] ADV start →", ret_adv)
            print("[BridgeAndroid] GATT start (cfg) →", gatt_cfg)
    
            self.running = True
            self.bt_enabled = True
    
        except Exception as e:
            print("[BridgeAndroid] error:", e)
            self.bt_enabled = False
    def stop(self):
        try:
            from jnius import autoclass
            autoclass("org.hackintosh1980.blebridge.AdvBridge").stop()
            autoclass("org.hackintosh1980.blebridge.GattBridge").stop()
            self.running = False
        except Exception:
            pass

    def get_status(self):
        return {
            "running": self.running,
            "bt_enabled": self.bt_enabled,
            "source": "android"
        }
# ------------------------------------------------------------
# 🖥️ Plattformwahl
# ------------------------------------------------------------
def get_bridge(prefer_mock=False) -> BridgeInterface:
    if platform == "android":
        return BleBridgeAndroid()
    return BridgeInterface()
