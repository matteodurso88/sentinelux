"""Bounded, scrollable diagnostics window for CPU temperature sensors."""

from __future__ import annotations

from typing import Any

from .metrics import TemperatureReading
from .presentation import format_temperature, sensor_display_name


class SensorDetailsWindow:
    """Read-only GTK window updated from the application's normal refresh."""

    def __init__(self, Gtk: Any) -> None:
        self.Gtk = Gtk
        self.signature: tuple[tuple[str, str], ...] | None = None
        self.value_labels: list[Any] = []

        self.window = Gtk.Window(title="Sentinelux · Sensori termici")
        self.window.set_default_size(420, 360)
        self.window.connect("delete-event", self._hide)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        root.set_border_width(12)
        self.window.add(root)

        self.summary_label = Gtk.Label(label="Sensori CPU · 0")
        self.summary_label.set_xalign(0)
        root.pack_start(self.summary_label, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        root.pack_start(scroller, True, True, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scroller.add(self.listbox)

    def update(self, readings: tuple[TemperatureReading, ...]) -> None:
        """Update values in place unless sensors were added/removed/renamed."""
        signature = tuple((reading.source, reading.label) for reading in readings)
        if signature != self.signature:
            for row in self.listbox.get_children():
                self.listbox.remove(row)
            self.value_labels.clear()

            for _reading in readings:
                label = self.Gtk.Label()
                label.set_xalign(0)
                label.set_margin_start(8)
                label.set_margin_end(8)
                label.set_margin_top(6)
                label.set_margin_bottom(6)
                self.listbox.add(label)
                self.value_labels.append(label)

            if not readings:
                fallback = self.Gtk.Label(label="Nessun sensore CPU disponibile")
                fallback.set_xalign(0)
                self.listbox.add(fallback)

            self.signature = signature
            self.listbox.show_all()

        self.summary_label.set_text(f"Sensori CPU · {len(readings)}")
        for label, reading in zip(self.value_labels, readings):
            label.set_text(
                f"{sensor_display_name(reading.label)} · "
                f"{format_temperature(reading.value_c)}"
            )
            label.set_tooltip_text(f"Sorgente: {reading.source}")

    def present(self) -> None:
        self.window.show_all()
        self.window.present()

    def _hide(self, *_: Any) -> bool:
        self.window.hide()
        return True
