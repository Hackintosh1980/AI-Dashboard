import os
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Rectangle, Color
from dashboard_gui.ui.dashboard_content.chart_tile import ChartTile
from dashboard_gui.ui.scaling_utils import dp_scaled


class DashboardMainPanel(GridLayout):
    def __init__(self, **kw):
        super().__init__(**kw)

        # --- Hintergrund ---
        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(
                source=os.path.join("assets", "background.png"),
                pos=self.pos,
                size=self.size
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.cols = 3
        self.spacing = dp_scaled(12)
        self.padding = dp_scaled(12)

        # ---------------------------------------------------
        # IN SENSORS
        # ---------------------------------------------------
        self.tile_temp_in = ChartTile(
            "Temperature IN", "—",
            [1, 0.2, 0.2, 1],
            bg="tile_bg_temp_in.png",
        )
        self.tile_hum_in = ChartTile(
            "Humidity IN", "%",
            [0.2, 0.6, 1, 1],
            bg="tile_bg_hum_in.png",
        )
        self.tile_vpd_in = ChartTile(
            "VPD IN", "kPa",
            [1, 0.8, 0.2, 1],
            bg="tile_bg_vpd_in.png",
        )

        # ---------------------------------------------------
        # EX SENSORS
        # ---------------------------------------------------
        self.tile_temp_ex = ChartTile(
            "Temperature EX", "—",
            [1, 0.4, 0.4, 1],
            bg="tile_bg_temp_out.png",
        )
        self.tile_hum_ex = ChartTile(
            "Humidity EX", "%",
            [0.3, 1, 1, 1],
            bg="tile_bg_hum_out.png",
        )
        self.tile_vpd_ex = ChartTile(
            "VPD EX", "kPa",
            [0.3, 1, 0.3, 1],
            bg="tile_bg_vpd_out.png",
        )

        # Map
        self.tile_map = {
            "temp_in": self.tile_temp_in,
            "hum_in":  self.tile_hum_in,
            "vpd_in":  self.tile_vpd_in,
            "temp_ex": self.tile_temp_ex,
            "hum_ex":  self.tile_hum_ex,
            "vpd_ex":  self.tile_vpd_ex,
        }

        # Anfang: alles anzeigen
        for tile in self.tile_map.values():
            self.add_widget(tile)

    # ============================================================
    # UPDATE – PURE MODE (decoded = Quelle, 1:1 übernehmen)
    # ============================================================
    def update_from_data(self, d):
        """
        Pure Multi-Channel Mode.
        Dashboard zieht Werte NUR aus dem gewählten Kanal:
            stream = d[d["channel"]]   # "adv" oder "gatt"
        """
    
        # -------------------------------------------------
        # 0) DEFAULT: ALLES AUS
        # -------------------------------------------------
        # WICHTIG:
        # Bei leerem / offline / ungültigem Frame
        # dürfen KEINE alten Tiles stehen bleiben
        self._apply_tile_visibility([])
    
        if not isinstance(d, dict):
            return
    
        # -------------------------------------------------
        # 1) Aktiven Kanal holen
        # -------------------------------------------------
        ch_name = d.get("channel")
        if ch_name not in ("adv", "gatt"):
            return
    
        stream = d.get(ch_name)
        if not isinstance(stream, dict):
            return
    
        # optional: explizit offline abfangen
        if not stream.get("alive", False):
            return
    
        internal = stream.get("internal", {})
        external = stream.get("external", {})
        vpd_int = stream.get("vpd_internal", {})
        vpd_ext = stream.get("vpd_external", {})
    
        active = []
    
        # -------------------------------------------------
        # INTERNAL
        # -------------------------------------------------
        if internal.get("temperature", {}).get("value") is not None:
            active.append("temp_in")
    
        if internal.get("humidity", {}).get("value") is not None:
            active.append("hum_in")
    
        if vpd_int.get("value") is not None:
            active.append("vpd_in")
    
        # -------------------------------------------------
        # EXTERNAL
        # -------------------------------------------------
        if external.get("present"):
            if external.get("temperature", {}).get("value") is not None:
                active.append("temp_ex")
    
            if external.get("humidity", {}).get("value") is not None:
                active.append("hum_ex")
    
            if vpd_ext.get("value") is not None:
                active.append("vpd_ex")
    
        # -------------------------------------------------
        # Sichtbarkeit anwenden (JETZT bewusst)
        # -------------------------------------------------
        self._apply_tile_visibility(active)
    
        # -------------------------------------------------
        # INTERNAL
        # -------------------------------------------------
        if "temp_in" in active:
            t = internal["temperature"]
            self.tile_temp_in.unit = t["unit"]
            self.tile_temp_in.update(t["value"])
    
        if "hum_in" in active:
            self.tile_hum_in.update(internal["humidity"]["value"])
    
        if "vpd_in" in active:
            self.tile_vpd_in.update(vpd_int["value"])
    
        # -------------------------------------------------
        # EXTERNAL
        # -------------------------------------------------
        if "temp_ex" in active:
            t = external["temperature"]
            self.tile_temp_ex.unit = t["unit"]
            self.tile_temp_ex.update(t["value"])
    
        if "hum_ex" in active:
            self.tile_hum_ex.update(external["humidity"]["value"])
    
        if "vpd_ex" in active:
            self.tile_vpd_ex.update(vpd_ext["value"])

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    # ============================================================
    # Sichtbarkeit
    # ============================================================
    def _apply_tile_visibility(self, active_keys):
        self.clear_widgets()

        order = [
            "temp_in", "hum_in", "vpd_in",
            "temp_ex", "hum_ex", "vpd_ex",
        ]

        for key in order:
            if key in active_keys:
                self.add_widget(self.tile_map[key])
