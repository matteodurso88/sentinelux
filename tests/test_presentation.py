from __future__ import annotations

import unittest

from sentinelux.alerts import ThermalState
from sentinelux.metrics import TemperatureReading
from sentinelux.presentation import (
    count_core_sensors,
    format_memory_summary,
    format_percentage,
    format_temperature,
    primary_cpu_sensor,
    sensor_count_summary,
    sensor_detail_names,
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

    def test_selects_package_before_core_and_tdie(self) -> None:
        readings = (
            TemperatureReading(80.0, "coretemp", "Core 0"),
            TemperatureReading(65.0, "coretemp", "Tdie"),
            TemperatureReading(70.0, "coretemp", "Package id 0"),
        )
        self.assertEqual(primary_cpu_sensor(readings), readings[2])

    def test_selects_tctl_fallback_but_not_core_as_package(self) -> None:
        readings = (
            TemperatureReading(65.0, "k10temp", "Core 0"),
            TemperatureReading(68.0, "k10temp", "Tctl"),
        )
        self.assertEqual(primary_cpu_sensor(readings), readings[1])
        self.assertIsNone(primary_cpu_sensor(readings[:1]))
        self.assertIsNone(primary_cpu_sensor(()))

    def test_core_count_excludes_package_and_sorts_sparse_hwmon_ids(self) -> None:
        readings = (
            TemperatureReading(52.0, "coretemp", "Package id 0"),
            TemperatureReading(42.0, "coretemp", "Core 12"),
            TemperatureReading(40.0, "coretemp", "Core 0"),
            TemperatureReading(41.0, "coretemp", "Core 4"),
        )
        self.assertEqual(count_core_sensors(readings), 3)
        self.assertEqual(
            sensor_count_summary(readings),
            "3 core monitorati · 4 sensori CPU",
        )
        self.assertEqual(
            sensor_detail_names(readings),
            ("CPU Package 0", "Core 3", "Core 1", "Core 2"),
        )

    def test_non_core_labels_are_never_counted_as_cores(self) -> None:
        readings = (
            TemperatureReading(55.0, "k10temp", "Tctl"),
            TemperatureReading(54.0, "k10temp", "Tdie"),
            TemperatureReading(52.0, "k10temp", "CPU 0"),
        )
        self.assertEqual(count_core_sensors(readings), 0)
        self.assertEqual(sensor_count_summary(readings), "Sensori CPU · 3")
        self.assertEqual(
            sensor_detail_names(readings),
            ("CPU Tctl", "CPU Tdie", "CPU 0"),
        )

    def test_exposes_state_label_and_colour(self) -> None:
        label, colour = thermal_state_presentation(ThermalState.CRITICAL)
        self.assertEqual(label, "Critico")
        self.assertEqual(colour, "#c62828")


if __name__ == "__main__":
    unittest.main()
