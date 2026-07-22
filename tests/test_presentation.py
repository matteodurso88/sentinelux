from __future__ import annotations

import unittest

from sentinelux.alerts import ThermalState
from sentinelux.presentation import (
    format_memory_summary,
    format_percentage,
    format_temperature,
    sensor_display_name,
    thermal_state_presentation,
)


class PresentationTests(unittest.TestCase):
    def test_formats_compact_values(self) -> None:
        self.assertEqual(format_percentage(12.34), "12.3%")
        self.assertEqual(format_temperature(61.25), "61.2 °C")
        self.assertEqual(format_temperature(None), "non disponibile")

    def test_formats_coherent_memory_summary(self) -> None:
        self.assertEqual(
            format_memory_summary(61.4, 2366 * 1024**2, 3840 * 1024**2, 1474 * 1024**2),
            "61.4% · 2.3 GiB / 3.8 GiB · disp. 1.4 GiB",
        )

    def test_normalises_package_and_core_names(self) -> None:
        self.assertEqual(sensor_display_name("Package id 0"), "CPU Package 0")
        self.assertEqual(sensor_display_name("Core 3"), "Core 3")
        self.assertEqual(sensor_display_name("Tctl"), "CPU Tctl")

    def test_keeps_unknown_sensor_name(self) -> None:
        self.assertEqual(sensor_display_name("CPU Die Average"), "CPU Die Average")

    def test_exposes_state_label_and_colour(self) -> None:
        label, colour = thermal_state_presentation(ThermalState.CRITICAL)
        self.assertEqual(label, "Critico")
        self.assertEqual(colour, "#c62828")


if __name__ == "__main__":
    unittest.main()
