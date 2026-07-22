from __future__ import annotations

import unittest
from collections import namedtuple

from sentinelux.metrics import (
    TemperatureReading,
    choose_cpu_temperature,
    choose_cpu_temperatures,
    collect_metrics,
    human_bytes,
)


class MetricsTests(unittest.TestCase):
    def test_prefers_cpu_over_nvme(self) -> None:
        selected = choose_cpu_temperature(
            [
                TemperatureReading(78.0, "nvme", "Composite"),
                TemperatureReading(62.0, "coretemp", "Package id 0"),
            ]
        )
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected.source, "coretemp")

    def test_keeps_package_and_all_core_readings(self) -> None:
        selected = choose_cpu_temperatures(
            [
                TemperatureReading(78.0, "nvme", "Composite"),
                TemperatureReading(62.0, "coretemp", "Package id 0"),
                TemperatureReading(60.0, "coretemp", "Core 0"),
                TemperatureReading(68.5, "coretemp", "Core 1"),
            ]
        )
        self.assertEqual(
            [reading.label for reading in selected],
            ["Package id 0", "Core 0", "Core 1"],
        )

    def test_prefers_hottest_cpu_sensor_for_policy(self) -> None:
        selected = choose_cpu_temperature(
            [
                TemperatureReading(60.0, "coretemp", "Core 0"),
                TemperatureReading(68.5, "coretemp", "Core 1"),
            ]
        )
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(selected.value_c, 68.5)
        self.assertEqual(selected.label, "Core 1")

    def test_rejects_implausible_values(self) -> None:
        selected = choose_cpu_temperature(
            [TemperatureReading(999.0, "coretemp", "Package id 0")]
        )
        self.assertIsNone(selected)

    def test_collect_metrics_exposes_average_and_sensor_list(self) -> None:
        Memory = namedtuple("Memory", "percent used available total")
        Swap = namedtuple("Swap", "percent used total")
        Sensor = namedtuple("Sensor", "label current")

        class FakePsutil:
            @staticmethod
            def virtual_memory():
                return Memory(50.0, 3 * 1024**3, 4 * 1024**3, 8 * 1024**3)

            @staticmethod
            def swap_memory():
                return Swap(25.0, 1 * 1024**3, 4 * 1024**3)

            @staticmethod
            def cpu_percent(interval=None):
                return 12.5

            @staticmethod
            def sensors_temperatures(fahrenheit=False):
                return {
                    "coretemp": [
                        Sensor("Package id 0", 61.0),
                        Sensor("Core 0", 59.0),
                        Sensor("Core 1", 67.0),
                    ]
                }

        metrics = collect_metrics(FakePsutil)
        self.assertEqual(metrics.memory_used_bytes, 3 * 1024**3)
        self.assertEqual(metrics.memory_available_bytes, 4 * 1024**3)
        self.assertEqual(metrics.memory_unavailable_bytes, 4 * 1024**3)
        self.assertEqual(metrics.memory_percent, 50.0)
        self.assertEqual(metrics.cpu_temperature_c, 67.0)
        self.assertAlmostEqual(metrics.cpu_temperature_average_c or 0, 62.3333, places=3)
        self.assertEqual(metrics.temperature_label, "Core 1")
        self.assertEqual(len(metrics.temperature_readings), 3)
        self.assertEqual(len(metrics.to_dict()["temperature_readings"]), 3)

    def test_memory_percent_is_derived_from_available_memory(self) -> None:
        Memory = namedtuple("Memory", "percent used available total")
        Swap = namedtuple("Swap", "percent used total")

        class FakePsutil:
            @staticmethod
            def virtual_memory():
                return Memory(99.0, 2 * 1024**3, 1 * 1024**3, 4 * 1024**3)

            @staticmethod
            def swap_memory():
                return Swap(0.0, 0, 0)

            @staticmethod
            def cpu_percent(interval=None):
                return 0.0

            @staticmethod
            def sensors_temperatures(fahrenheit=False):
                return {}

        metrics = collect_metrics(FakePsutil)
        self.assertEqual(metrics.memory_unavailable_bytes, 3 * 1024**3)
        self.assertEqual(metrics.memory_percent, 75.0)

    def test_human_bytes(self) -> None:
        self.assertEqual(human_bytes(0), "0 B")
        self.assertEqual(human_bytes(1024), "1.0 KiB")
        self.assertEqual(human_bytes(1024**3), "1.0 GiB")


if __name__ == "__main__":
    unittest.main()
