# -*- coding: utf-8 -*-
"""
SettingsMainPanel – Scrollbare Version (Setup-Style)
Perfekt kompatibel mit SettingsScreen
© 2025 Dominik Rosenthal (Hackintosh1980)
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.button import Button

from dashboard_gui.ui.scaling_utils import dp_scaled, sp_scaled
import config


class SettingsMainPanel(BoxLayout):

    def __init__(self, on_save, on_cancel, **kw):
        super().__init__(**kw)

        self.orientation = "vertical"
        self.spacing = dp_scaled(10)
        self.padding = dp_scaled(12)

        self.on_save = on_save
        self.on_cancel = on_cancel

        # ------------------------------------------
        # Load config
        # ------------------------------------------
        self.cfg = config._init()
        self.inputs = {}

        # ------------------------------------------
        # Scroll Area
        # ------------------------------------------
        scroll = ScrollView(size_hint=(1, 1))
        container = GridLayout(
            cols=1,
            spacing=dp_scaled(12),
            padding=[0, dp_scaled(6), 0, dp_scaled(6)],
            size_hint_y=None
        )
        container.bind(minimum_height=container.setter("height"))

        # helper: add slider
        def add_slider(label_text, key, min_v, max_v, step):
            row = BoxLayout(
                size_hint_y=None,
                height=dp_scaled(48),
                spacing=dp_scaled(10)
            )

            lbl = Label(
                text=label_text,
                size_hint=(0.35, 1),
                font_size=sp_scaled(16)
            )

            slider = Slider(
                min=min_v,
                max=max_v,
                step=step,
                value=float(self.cfg.get(key, 0)),
                size_hint=(0.45, 1)
            )

            val = Label(
                text=str(self.cfg.get(key, 0)),
                size_hint=(0.20, 1),
                font_size=sp_scaled(16)
            )

            slider.bind(value=lambda inst, v, lab=val: setattr(lab, "text", f"{v:.1f}"))

            self.inputs[key] = slider

            row.add_widget(lbl)
            row.add_widget(slider)
            row.add_widget(val)
            container.add_widget(row)

        # sliders
        add_slider("Refresh Interval", "refresh_interval", 0.5, 10, 0.5)
        add_slider("UI Refresh", "ui_refresh_interval", 0.1, 5, 0.1)
        add_slider("Stale Timeout", "stale_timeout", 5, 60, 1)
        add_slider("Temp Offset", "temperature_offset", -10, 10, 0.1)
        add_slider("Humidity Offset", "humidity_offset", -20, 20, 1)
        add_slider("Leaf Offset", "leaf_offset", -10, 10, 0.1)

        # ------------------------------------------
        # UNIT TOGGLE
        # ------------------------------------------
        toggle_row = BoxLayout(
            size_hint_y=None, height=dp_scaled(48),
            spacing=dp_scaled(10)
        )

        toggle_row.add_widget(Label(
            text="Temperature Unit",
            size_hint=(0.35, 1),
            font_size=sp_scaled(16)
        ))

        self.temp_unit = self.cfg.get("temperature_unit", "C")

        self.btn_C = Button(
            text="°C",
            font_size=sp_scaled(18),
            background_color=(0.4, 0.7, 1, 1) if self.temp_unit == "C" else (0.3, 0.3, 0.3, 1)
        )
        self.btn_F = Button(
            text="°F",
            font_size=sp_scaled(18),
            background_color=(0.4, 0.7, 1, 1) if self.temp_unit == "F" else (0.3, 0.3, 0.3, 1)
        )

        self.btn_C.bind(on_release=lambda *_: self._set_unit("C"))
        self.btn_F.bind(on_release=lambda *_: self._set_unit("F"))

        toggle_row.add_widget(self.btn_C)
        toggle_row.add_widget(self.btn_F)
        container.add_widget(toggle_row)

        # Add scroll container
        scroll.add_widget(container)
        self.add_widget(scroll)

        # ------------------------------------------
        # Bottom buttons
        # ------------------------------------------
        btn_row = BoxLayout(
            size_hint_y=None,
            height=dp_scaled(36),
            spacing=dp_scaled(10)
        )

        btn_reset = Button(
            text="Reset Defaults",
            font_size=sp_scaled(16),
            background_color=(0.45, 0.45, 0.45, 1)
        )
        btn_reset.bind(on_release=lambda *_: self._reset_defaults())

        btn_save = Button(
            text="Save",
            font_size=sp_scaled(18),
            background_color=(0.2, 0.55, 0.2, 1)
        )
        btn_save.bind(on_release=lambda *_: self.on_save(self._collect()))

        btn_cancel = Button(
            text="Cancel",
            font_size=sp_scaled(18),
            background_color=(0.55, 0.2, 0.2, 1)
        )
        btn_cancel.bind(on_release=lambda *_: self.on_cancel())

        btn_row.add_widget(btn_reset)
        btn_row.add_widget(btn_save)
        btn_row.add_widget(btn_cancel)
        self.add_widget(btn_row)

    # ------------------------------------------
    # Temperature unit toggle
    # ------------------------------------------
    def _set_unit(self, u):
        self.temp_unit = u
        self.btn_C.background_color = (0.4, 0.7, 1, 1) if u == "C" else (0.3, 0.3, 0.3, 1)
        self.btn_F.background_color = (0.4, 0.7, 1, 1) if u == "F" else (0.3, 0.3, 0.3, 1)

    # ------------------------------------------
    # Defaults
    # ------------------------------------------
    def _reset_defaults(self):
        defaults = {
            "refresh_interval": 2.0,
            "ui_refresh_interval": 1.0,
            "stale_timeout": 15.0,
            "temperature_offset": 0.0,
            "humidity_offset": 0.0,
            "leaf_offset": 0.0,
            "temperature_unit": "C",
        }

        for k, v in defaults.items():
            if k == "temperature_unit":
                self._set_unit(v)
                continue
            if k in self.inputs:
                self.inputs[k].value = v

    # ------------------------------------------
    # Collect all results
    # ------------------------------------------
    def _collect(self):
        out = {key: inp.value for key, inp in self.inputs.items()}
        out["temperature_unit"] = self.temp_unit
        return out
