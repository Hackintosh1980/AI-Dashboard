from kivy.core.window import Window
from kivy.metrics import dp, sp
import sys


# -------------------------------------------------------
# 🖥️ Desktop Window-Startwert (BEVOR compute_ui_scale)
# -------------------------------------------------------
if sys.platform not in ("android", "ios"):
    try:
        Window.size = (1400, 800)
        Window.minimum_width = 900
        Window.minimum_height = 600
    except Exception:
        pass


# -------------------------------------------------------
# 🔧 Global UI scale berechnet aus Window DPI/Size
# -------------------------------------------------------
def compute_ui_scale():
    import sys

    try:
        w, h = Window.size
        dpi = Window.dpi or 96.0
    except Exception:
        w, h, dpi = 1400.0, 800.0, 96.0

    # Desktop bleibt exakt 1.0 (Referenz)
    if sys.platform not in ("android", "ios"):
        return 1.0

    # ---------------------------------------------------
    #  TEST-BEREICH ① — BASIS FAKTOR (Hauptregler!)
    # ---------------------------------------------------
    BASE = 0.78     # <<< HIER testen: 0.70 / 0.72 / 0.75 / 0.78 / 0.80


    # ---------------------------------------------------
    #  TEST-BEREICH ② — DPI-Faktor (Feinjustage)
    # ---------------------------------------------------
    density_factor = dpi / 420.0       # <<< HIER ändern: 380 / 420 / 480
    density_factor = max(0.85, min(density_factor, 1.1))


    # ---------------------------------------------------
    #  TEST-BEREICH ③ — Breiten-Faktor (Feinjustage)
    # ---------------------------------------------------
    geom_factor = min(w / 1080.0, 1.0)   # <<< HIER ändern: 1080 / 1200 / 1440
    geom_factor = max(0.85, geom_factor)


    # ---------------------------------------------------
    #  Ergebnis
    # ---------------------------------------------------
    raw = BASE * density_factor * geom_factor

    # ---------------------------------------------------
    #  TEST-BEREICH ④ — End-Clamp (Safety)
    # ---------------------------------------------------
    return max(0.70, min(raw, 0.90))     # <<< untere/obere Grenzen ändern möglich

UI_SCALE = compute_ui_scale()


def dp_scaled(v: float) -> float:
    return dp(v * UI_SCALE)


def sp_scaled(v: float) -> float:
    return sp(v * UI_SCALE)
