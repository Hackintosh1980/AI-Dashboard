from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.metrics import dp

PROFILES = ["unknown", "tb2", "tpro"]

class DeviceRow(BoxLayout):
    def __init__(self, mac, text, profile, on_select, on_profile, **kw):
        super().__init__(orientation="horizontal", padding=[10, 10], spacing=10, **kw)

        self.mac = mac
        self.on_select = on_select
        self.on_profile = on_profile
        self.selected = False

        self.label = Label(
            text=text,
            halign="left",
            valign="middle",
            font_size=dp(18),
            color=(1, 1, 1, 1),
            size_hint_x=0.65,
        )
        self.add_widget(self.label)

        self.spinner = Spinner(
            text=profile,
            values=PROFILES,
            size_hint_x=0.35,
            background_color=(0.1,0.1,0.1,1),
            color=(0.9,0.9,0.9,1),
        )
        self.spinner.bind(text=self._profile_changed)
        self.add_widget(self.spinner)

        self.height = dp(50)
        self.size_hint_y = None
        self.update_color()

    def update_color(self):
        if self.selected:
            # sanftes Grün für "ausgewählt"
            self.label.color = (0.3, 1.0, 0.3, 1)
            self.spinner.background_color = (0.1, 0.3, 0.1, 1)
        else:
            # normaler Zustand
            self.label.color = (1, 1, 1, 1)
            self.spinner.background_color = (0.1, 0.1, 0.1, 1)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.selected = not self.selected
            self.update_color()
            self.on_select(self.mac, self.selected)
            return True
        return super().on_touch_up(touch)

    def _profile_changed(self, spinner, value):
        self.on_profile(self.mac, value)
