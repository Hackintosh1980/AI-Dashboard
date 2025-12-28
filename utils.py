#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
utils.py – RECYCLED from old ThermoDashboard
© Dominik Rosenthal

Enthält NUR:
• °C <-> °F
• Temperatur-Offset
• Humidity-Offset
• Leaf-Offset
• VPD / SVP wie alte Version
• Android-4095-Fix
• Externe-Sonde-Prüfung
"""

import math
import config


# ------------------------------------------------------------
# 🔥 4095 / FFFF Bug-Fix (alter Code)
# ------------------------------------------------------------
def fix_android_value(v):
    """
    Alte Regel:
    Wenn ThermoBeacon negative Werte sendet → 4095
    Dann bedeutet das: kein Messwert

    Rückgabe:
      None = invalid
      float = korrekt
    """
    if v is None:
        return None

    # altes Verhalten übernommen
    if v >= 4095:
        return None

    return float(v)


# ------------------------------------------------------------
# 🌡 Offset + Unit (alte Logik)
# ------------------------------------------------------------
def apply_temperature_offset(t):
    if t is None:
        return None
    return float(t) + float(config.get_temperature_offset())


def apply_humidity_offset(h):
    if h is None:
        return None
    return float(h) + float(config.get_humidity_offset())


def apply_leaf_offset(t):
    if t is None:
        return None
    return float(t) + float(config.get_leaf_offset())


# ------------------------------------------------------------
# 🌡 °C <-> °F (alte unveränderte Formeln)
# ------------------------------------------------------------
def c_to_f(c):
    if c is None:
        return None
    return c * 9.0 / 5.0 + 32.0


def f_to_c(f):
    if f is None:
        return None
    return (f - 32.0) * 5.0 / 9.0


def apply_unit(t_c):
    """
    Alte Logik:
    config.temperature_unit in {"C", "F"}
    """
    if t_c is None:
        return None

    unit = config.get_temperature_unit()
    return t_c if unit == "C" else c_to_f(t_c)


# ------------------------------------------------------------
# 💧 SVP / VPD (alte Originalformeln)
# ------------------------------------------------------------
def saturation_vapor_pressure(t_c):
    """
    Alte Formel:
    SVP = 610.78 * exp(17.269 * T / (T + 237.3))
    Ergebnis in Pa
    """
    if t_c is None:
        return None
    return 610.78 * math.exp((17.269 * t_c) / (t_c + 237.3))


def vpd(t_c, rh):
    """
    Alter Code:
    VPD = (1 - RH/100) * SVP
    Ausgabe in kPa
    """
    if t_c is None or rh is None:
        return None
    svp = saturation_vapor_pressure(t_c)  # Pa
    return (1.0 - (rh / 100.0)) * svp / 1000.0  # kPa


# ------------------------------------------------------------
# 🧪 Externe Sonde prüfen (alte Regeln)
# ------------------------------------------------------------
def external_present(h_ext):
    """
    Alte Regeln:
    - RH <= 0.1 → keine Sonde
    - RH > 110 → keine Sonde
    - None → keine Sonde
    """
    if h_ext is None:
        return False
    if h_ext <= 0.1:
        return False
    if h_ext > 110:
        return False
    return True
