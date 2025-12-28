import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy_garden.graph import Graph, LinePlot
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Rectangle, Color

from dashboard_gui.ui.scaling_utils import dp_scaled, sp_scaled
from dashboard_gui.global_state_manager import GLOBAL_STATE


class ChartTile(ButtonBehavior, BoxLayout):

    def __init__(self, title, unit, color_rgba, bg=None, **kw):
        ButtonBehavior.__init__(self)
        BoxLayout.__init__(
            self,
            orientation="vertical",
            spacing=dp_scaled(6),
            padding=dp_scaled(6),
            **kw
        )
        self._last_unit = unit
        self.title = title
        self.unit = unit
        self.color = color_rgba
        self.window = 120
        self.buffer = []
        self.last_value = None
        self.smoothing = 0.25
        # Multi-Device Buffers: device_id → eigener Verlauf
        self.buffers = {}
        # -------------------------------------------------
        # BACKGROUND
        # -------------------------------------------------
        if bg:
            self.bg_path = os.path.join("dashboard_gui", "assets", "tiles", bg)
        else:
            self.bg_path = None

        with self.canvas.before:
            if self.bg_path:
                self.bg_rect = Rectangle(source=self.bg_path, pos=self.pos, size=self.size)
            else:
                Color(0, 0, 0, 0)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._upd_bg, size=self._upd_bg)
        self.base_unit = unit   # z. B. "°C" oder "kPa"

        # -------------------------------------------------
        # HEADER (TITLE • TREND • VALUE)
        # -------------------------------------------------
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp_scaled(38),
            spacing=dp_scaled(4),
        )

        self.lbl_title = Label(text=title, font_size=sp_scaled(16))
        self.lbl_trend = Label(text="", font_size=sp_scaled(18), font_name="FA")
        self.lbl_value = Label(text="--", font_size=sp_scaled(18))

        header.add_widget(self.lbl_title)
        header.add_widget(self.lbl_trend)
        header.add_widget(self.lbl_value)
        self.add_widget(header)

        # -------------------------------------------------
        # GRAPH
        # -------------------------------------------------
        self.graph = Graph(
            xlabel="", ylabel="",
            x_ticks_major=0, x_ticks_minor=0,
            y_ticks_major=0, y_ticks_minor=0,
            x_grid_label=False, y_grid_label=False,
            draw_border=False,
            padding=dp_scaled(4),
            xmin=0, xmax=self.window,
            ymin=0, ymax=1,
            background_color=(0, 0, 0, 0),
            tick_color=(0, 0, 0, 0),
            size_hint=(1, 1),
        )

        self.plot = LinePlot(color=self.color, line_width=2.0)
        self.graph.add_plot(self.plot)

        glow = [self.color[0], self.color[1], self.color[2], 0.25]
        self.plot_glow = LinePlot(color=glow, line_width=5.0)
        self.graph.add_plot(self.plot_glow)

        self.add_widget(self.graph)

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------
        footer = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp_scaled(22),
            spacing=dp_scaled(4),
        )

        self.lbl_avg = Label(text="avg: --", font_size=sp_scaled(12))
        self.lbl_minmax = Label(text="", font_size=sp_scaled(12))

        footer.add_widget(self.lbl_avg)
        footer.add_widget(self.lbl_minmax)

        self.add_widget(footer)


    # -------------------------------------------------
    # BACKGROUND UPDATE
    # -------------------------------------------------
    def _upd_bg(self, *_):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------
    def update(self, value):
        if value is None:
            self.reset()
            return
        # -------------------------------------------------
        # UNIT SWITCH DETECT → RESCALE BUFFER
        # -------------------------------------------------
        if self.unit != self._last_unit:
            if self._last_unit == "°C" and self.unit == "°F":
                # °C → °F
                for k, buf in self.buffers.items():
                    self.buffers[k] = [(v * 9 / 5) + 32 for v in buf]
            elif self._last_unit == "°F" and self.unit == "°C":
                # °F → °C
                for k, buf in self.buffers.items():
                    self.buffers[k] = [(v - 32) * 5 / 9 for v in buf]
        
            self._last_unit = self.unit    
        # --- DEVICE + CHANNEL ERMITTELN ---
        from dashboard_gui.global_state_manager import GLOBAL_STATE
        from dashboard_gui.data_buffer import BUFFER
    
        data = BUFFER.get()
        if not data:
            return
    
        active = GLOBAL_STATE.active_index
        if active >= len(data):
            return
    
        device_id = data[active].get("device_id")
        if device_id is None:
            return
    
        # Aktiver Kanal: "adv" oder "gatt"
        active_channel = GLOBAL_STATE.get_active_channel()
    
        # Multi-Channel Buffer Key
        buf_key = f"{device_id}_{active_channel}"
    
        # Buffer initialisieren
        if buf_key not in self.buffers:
            self.buffers[buf_key] = []
    
        buf = self.buffers[buf_key]
    
        # --- VALUE PARSEN (KANONISCH) ---
        try:
            v = float(value)
        except:
            return
        
        # ❗ WICHTIG:
        # value MUSS immer in base_unit geliefert werden
        # (z. B. °C, nicht °F)
    
        # --- Glättung ---
        if len(buf) == 0:
            smoothed = v
        else:
            smoothed = (buf[-1] * (1 - self.smoothing)) + (v * self.smoothing)
    
        # --- Trend ---
        if len(buf) > 1:
            diff = smoothed - buf[-1]
            if diff > 0.01:
                self.lbl_trend.text = "\uf062"   # up
            elif diff < -0.01:
                self.lbl_trend.text = "\uf063"   # down
            else:
                self.lbl_trend.text = "\uf061"   # right
            self.lbl_trend.color = (0.7, 0.7, 0.7, 1)
    
        # --- Aktueller Wert ---
        display_value = smoothed
        
        # Einheit nur fürs Anzeigen konvertieren
        if self.base_unit == "°C" and self.unit == "°F":
            display_value = (smoothed * 9 / 5) + 32
        
        self.lbl_value.text = f"{display_value:.2f} {self.unit}"    
        # --- Write to buffer ---
        buf.append(smoothed)
        if len(buf) > self.window:
            buf.pop(0)
    
        # --- Graph update ---
        self._render_buffer(buf)
        
    def _render_buffer(self, buf):
        pts = [(i, val) for i, val in enumerate(buf)]
        self.plot.points = pts
        self.plot_glow.points = pts
    
        if len(buf) > 1:
            mn = min(buf)
            mx = max(buf)
            if mn == mx:
                mn -= 0.5
                mx += 0.5
            margin = (mx - mn) * 0.2
            self.graph.ymin = mn - margin
            self.graph.ymax = mx + margin
    
        self.graph.xmax = max(self.window, len(buf))
    
        # Footer
        if len(buf) > 1:
            avg_v = sum(buf) / len(buf)
            mn = min(buf)
            mx = max(buf)
            self.lbl_avg.text = f"avg: {avg_v:.2f}"
            self.lbl_minmax.text = f"min: {mn:.2f}  max: {mx:.2f}"
        else:
            self.lbl_avg.text = "avg: --"
            self.lbl_minmax.text = ""

    # -------------------------------------------------
    # RESET
    # -------------------------------------------------
    def reset(self):
        self.lbl_value.text = "--"
        self.lbl_trend.text = ""
        self.lbl_avg.text = "avg: --"
        self.lbl_minmax.text = ""

        self.buffers = {}
        self.last_value = None
        self.plot.points = []
        self.plot_glow.points = []
        self.graph.ymin = 0
        self.graph.ymax = 1

    # -------------------------------------------------
    # TILE CLICK → FULLSCREEN
    # -------------------------------------------------
    def on_release(self, *_):
        parent = self.parent
        sm = None
        while parent:
            if hasattr(parent, "current") and hasattr(parent, "get_screen"):
                sm = parent
                break
            parent = parent.parent

        if sm is None:
            print("❌ ERROR: Kein ScreenManager gefunden!")
            return

        if not sm.has_screen("fullscreen"):
            print("❌ ERROR: Fullscreen existiert nicht!")
            return

        dashboard = sm.get_screen("dashboard")
        for key, tile in dashboard.content.tile_map.items():
            if tile is self:
                fs = sm.get_screen("fullscreen")
                fs.activate_tile(key)
                sm.current = "fullscreen"
                return

        print("❌ ERROR: Tile-Key nicht gefunden!")
