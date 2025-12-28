# dashboard_gui/ui/cam_viewer_content/cam_player_widget.py

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.uix.image import Image
from kivy.clock import Clock

class CamPlayerWidget(BoxLayout):
    """
    Desktop:
        - kein eigenes Video, ffplay öffnet extern
        - hier im Panel nur Text "Live wird extern angezeigt"

    Android:
        - RTSP nicht möglich → Platzhalter mit Icon/Text
    """

    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"

        if platform == "android":
            # --- Platzhalter ---
            self.placeholder = Label(
                text="📷 Live-Stream auf Android nicht verfügbar\n(Externe RTSP-Dekodierung nötig)",
                halign="center",
                valign="middle",
                font_size="20sp"
            )
            self.add_widget(self.placeholder)

        else:
            # --- Desktop ---
            self.info = Label(
                text="▶ Live-Stream startet im externen Fenster (ffplay)",
                halign="center",
                valign="middle",
                font_size="18sp"
            )
            self.add_widget(self.info)

    def show_starting(self, url):
        if platform != "android":
            self.info.text = f"Starte ffplay…\n{url}"
        else:
            self.placeholder.text = "Android: kein interner RTSP Player verfügbar."

    def show_stopped(self):
        if platform != "android":
            self.info.text = "Live-Stream gestoppt."
        else:
            self.placeholder.text = "📷 Kein Live-Stream aktiv."
