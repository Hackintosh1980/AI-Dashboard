# device_picker.py – Pretty Picker, Session 17/18 safe

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from dashboard_gui.global_state_manager import GLOBAL_STATE
from dashboard_gui.data_buffer import BUFFER


class PickerRow(ButtonBehavior, BoxLayout):
    """
    Schöner Einzel-Button mit Kachelhaptik.
    """
    def __init__(self, text, idx, callback, **kw):
        super().__init__(**kw)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = [dp(14), 0]
        self.idx = idx
        self.callback = callback

        self.label = Label(
            text=text,
            halign="left",
            valign="middle",
            size_hint=(1, 1)
        )
        self.add_widget(self.label)

        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            self._color = Color(0.18, 0.18, 0.18, 1)
            self._bg = RoundedRectangle(radius=[dp(10)])

        self.bind(pos=self._update_bg, size=self._update_bg)

    def on_release(self):
        self.callback(self.idx)

    def on_press(self):
        self._color.rgba = (0.28, 0.28, 0.28, 1)

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        self._color.rgba = (0.18, 0.18, 0.18, 1)

    def _update_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size



class DevicePickerScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)

        root = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(12))
        self.add_widget(root)

        # HEADER – Mini-Leiste
        header = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(45),
            padding=[0, 0, 0, 0]
        )

        lbl = Label(
            text="Geräte-Auswahl",
            font_size=dp(18),
            bold=True
        )
        header.add_widget(lbl)

        root.add_widget(header)

        # Scroll
        scroll = ScrollView(size_hint=(1, 1))
        root.add_widget(scroll)

        # Innerer Container
        self.list_container = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )
        self.list_container.bind(minimum_height=self.list_container.setter("height"))
        scroll.add_widget(self.list_container)

        # Zurück-Button
        self.btn_back = Button(
            text="←  Zurück",
            size_hint=(1, None),
            height=dp(48)
        )
        self.btn_back.bind(on_release=lambda *_: self._go_back())
        root.add_widget(self.btn_back)


    def on_pre_enter(self, *_):
        self._rebuild_list()


    def _rebuild_list(self):
        self.list_container.clear_widgets()

        BUFFER.soft_reload()
        data = BUFFER.get()

        if not data or not isinstance(data, list):
            return

        for i, dev in enumerate(data):
            mac = dev.get("device_id_flat") or dev.get("device_id")

            row = PickerRow(
                text=f"{i+1}.  {mac}",
                idx=i,
                callback=self._pick
            )
            self.list_container.add_widget(row)


    def _pick(self, idx):
        print(f"[PICKER] Selected device index {idx}")
        GLOBAL_STATE.set_active_index(idx)
        self._go_back()


    def _go_back(self):
        self.manager.current = "dashboard"
