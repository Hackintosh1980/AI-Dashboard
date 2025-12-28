#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.clipboard import Clipboard


class IndentGUI(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=10, padding=10, **kwargs)

        # -----------------------------
        # OBERER BEREICH – 2 SPALTEN
        # -----------------------------
        body = BoxLayout(orientation="horizontal", spacing=10)

        # Eingabe
        self.input_box = TextInput(
            text="",
            multiline=True,
            font_size=16
        )

        # Ausgabe
        self.output_box = TextInput(
            text="",
            multiline=True,
            readonly=True,
            font_size=16
        )

        body.add_widget(self.input_box)
        body.add_widget(self.output_box)

        # -----------------------------
        # CONTROLS Unten
        # -----------------------------
        controls = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=0.15)

        btn_m4 = Button(text="-4", on_release=lambda *_: self.apply_indent(-4))
        btn_m2 = Button(text="-2", on_release=lambda *_: self.apply_indent(-2))
        btn_p2 = Button(text="+2", on_release=lambda *_: self.apply_indent(2))
        btn_p4 = Button(text="+4", on_release=lambda *_: self.apply_indent(4))
        btn_copy = Button(text="COPY", on_release=self.copy_result)

        for b in (btn_m4, btn_m2, btn_p2, btn_p4, btn_copy):
            controls.add_widget(b)

        # Vollständiges Layout
        self.add_widget(body)
        self.add_widget(controls)

    # -------------------------------------------------------------
    # EINRÜCKUNG
    # -------------------------------------------------------------
    def apply_indent(self, spaces):
        raw = self.input_box.text.split("\n")
        abs_sp = abs(spaces)
        prefix = " " * abs_sp

        result = []

        if spaces > 0:
            # Einrücken
            for line in raw:
                result.append(prefix + line)
        else:
            # Ausrücken
            for line in raw:
                if line.startswith(prefix):
                    result.append(line[abs_sp:])
                else:
                    result.append(line)

        self.output_box.text = "\n".join(result)

    # -------------------------------------------------------------
    # COPY → CLIPBOARD
    # -------------------------------------------------------------
    def copy_result(self, *_):
        Clipboard.copy(self.output_box.text)


class IndentApp(App):
    def build(self):
        return IndentGUI()


if __name__ == "__main__":
    IndentApp().run()
