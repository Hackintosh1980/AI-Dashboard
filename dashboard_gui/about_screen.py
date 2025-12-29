# dashboard_gui/about_screen.py
# © 2025 Dominik Rosenthal (Hackintosh1980)

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
import time

from dashboard_gui.ui.common.header_online import HeaderBar
from dashboard_gui.ui.scaling_utils import dp_scaled, sp_scaled


class AboutScreen(Screen):
    name = "about"

    def __init__(self, **kw):
        super().__init__(**kw)

        from dashboard_gui.global_state_manager import GLOBAL_STATE
        GLOBAL_STATE.attach_about(self)

        root = BoxLayout(orientation="vertical")

        # HEADER
        self.header = HeaderBar(
            goto_setup=lambda *_: setattr(self.manager, "current", "setup"),
            goto_debug=lambda *_: setattr(self.manager, "current", "debug"),
            goto_device_picker=lambda *_: setattr(self.manager, "current", "device_picker"),
        )
        self.header.lbl_title.text = "About"
        self.header.update_back_button("about")
        root.add_widget(self.header)

        # BODY
        body = BoxLayout(
            orientation="vertical",
            padding=dp_scaled(20),
            spacing=dp_scaled(12)
        )

        body.add_widget(Label(
            text="AI Dashboard 1.24",
            font_size=sp_scaled(28),
            bold=True
        ))



        body.add_widget(Label(
            text=(
                "AI Dashboard 1.24\n\n"
                "AI Dashboard is a cross-platform monitoring and analysis system\n"
                "for Bluetooth Low Energy (BLE) sensors.\n\n"
                "It unifies data from different manufacturers and protocols\n"
                "(ADV, GATT, hybrid devices) into a single, consistent data model.\n\n"
                "The system is designed around real-time signals, explicit control\n"
                "and transparent configuration — no hidden automation.\n\n"
                "AI Dashboard focuses on understanding devices as they behave,\n"
                "not forcing them into simplified abstractions."
                "Bluetooth is required to discover and read your sensors.\n"
                "Please enable Bluetooth and grant the requested permissions to continue."
            ),
            font_size=sp_scaled(16),
            halign="left",
            valign="top"
        ))

        body.add_widget(Label(
            text="© 2025 Dominik Rosenthal (Hackintosh1980)",
            font_size=sp_scaled(16),
            color=(0.8, 0.8, 0.8, 1)
        ))

        root.add_widget(body)
        self.add_widget(root)

    def update_from_global(self, d):
        self.header.update_from_global(d)