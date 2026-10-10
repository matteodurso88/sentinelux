"""Headless tests for the GTK sensor window's refresh behavior."""

from __future__ import annotations

import unittest

from sentinelux.metrics import TemperatureReading
from sentinelux.sensor_details import SensorDetailsWindow


class FakeWidget:
    def __init__(self, *args, label="", **kwargs):
        self.children = []
        self.text = label
        self.visible = False

    def __getattr__(self, name):
        if name.startswith("set_") or name in {"connect", "present"}:
            return lambda *args, **kwargs: None
        raise AttributeError(name)

    def add(self, child):
        self.children.append(child)

    def pack_start(self, child, *args):
        self.add(child)

    def remove(self, child):
        self.children.remove(child)

    def get_children(self):
        return tuple(self.children)

    def show_all(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def set_text(self, value):
        self.text = value


class FakeGtk:
    Window = FakeWidget
    Box = FakeWidget
    Label = FakeWidget
    ScrolledWindow = FakeWidget
    ListBox = FakeWidget

    class Orientation:
        VERTICAL = object()

    class PolicyType:
        NEVER = object()
        AUTOMATIC = object()

    class SelectionMode:
        NONE = object()


class SensorDetailsTests(unittest.TestCase):
    def readings(self, count: int) -> tuple[TemperatureReading, ...]:
        return tuple(
            TemperatureReading(40.0 + i, "coretemp", f"Core {i}")
            for i in range(count)
        )

    def test_scrolling_model_keeps_all_core_rows(self) -> None:
        details = SensorDetailsWindow(FakeGtk)
        for count in (4, 8, 16, 32):
            details.update(self.readings(count))
            self.assertEqual(len(details.value_labels), count)
            self.assertEqual(len(details.listbox.get_children()), count)
            self.assertEqual(details.summary_label.text, f"Sensori CPU · {count}")

    def test_refresh_changes_values_without_rebuilding_rows(self) -> None:
        details = SensorDetailsWindow(FakeGtk)
        details.update(self.readings(16))
        before = list(details.value_labels)
        refreshed = tuple(
            TemperatureReading(60.0 + i, "coretemp", f"Core {i}")
            for i in range(16)
        )
        details.update(refreshed)
        self.assertEqual(details.value_labels, before)
        self.assertIn("60.0 °C", details.value_labels[0].text)
        self.assertIn("75.0 °C", details.value_labels[-1].text)

    def test_missing_sensors_then_reappear(self) -> None:
        details = SensorDetailsWindow(FakeGtk)
        details.update(())
        self.assertEqual(len(details.listbox.get_children()), 1)
        self.assertEqual(details.value_labels, [])
        details.update(self.readings(4))
        self.assertEqual(len(details.value_labels), 4)


if __name__ == "__main__":
    unittest.main()
