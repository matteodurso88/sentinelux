from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sentinelux.protection import (
    ProtectionEventKind,
    ThermalProtectionController,
    format_kernel_trip_summary,
    read_kernel_critical_trips,
    request_sleep_action,
    sleep_action_capability,
)


class ThermalProtectionControllerTests(unittest.TestCase):
    def test_requires_persistent_temperature_before_trigger(self) -> None:
        controller = ThermalProtectionController(
            enabled=True,
            threshold_c=95.0,
            persistence_seconds=20.0,
            recovery_hysteresis_c=3.0,
            action="hibernate",
        )
        armed = controller.evaluate(96.0, 100.0)
        self.assertIsNotNone(armed)
        self.assertEqual(armed.kind, ProtectionEventKind.ARMED)
        self.assertIsNone(controller.evaluate(96.0, 119.9))
        triggered = controller.evaluate(96.0, 120.0)
        self.assertIsNotNone(triggered)
        self.assertEqual(triggered.kind, ProtectionEventKind.TRIGGERED)
        self.assertIsNone(controller.evaluate(97.0, 130.0))

    def test_recovery_cancels_pending_action(self) -> None:
        controller = ThermalProtectionController(
            enabled=True,
            threshold_c=95.0,
            persistence_seconds=20.0,
            recovery_hysteresis_c=3.0,
            action="hibernate",
        )
        controller.evaluate(96.0, 10.0)
        self.assertIsNone(controller.evaluate(93.0, 12.0))
        cancelled = controller.evaluate(92.0, 13.0)
        self.assertIsNotNone(cancelled)
        self.assertEqual(cancelled.kind, ProtectionEventKind.CANCELLED)

    def test_disabled_controller_never_arms(self) -> None:
        controller = ThermalProtectionController(
            enabled=False,
            threshold_c=95.0,
            persistence_seconds=20.0,
            recovery_hysteresis_c=3.0,
            action="hibernate",
        )
        self.assertIsNone(controller.evaluate(110.0, 10.0))


class KernelTripTests(unittest.TestCase):
    def test_reads_only_critical_trip_points(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            zone = root / "thermal_zone0"
            zone.mkdir()
            (zone / "type").write_text("x86_pkg_temp\n", encoding="utf-8")
            (zone / "trip_point_0_type").write_text("passive\n", encoding="utf-8")
            (zone / "trip_point_0_temp").write_text("85000\n", encoding="utf-8")
            (zone / "trip_point_1_type").write_text("critical\n", encoding="utf-8")
            (zone / "trip_point_1_temp").write_text("100000\n", encoding="utf-8")

            trips = read_kernel_critical_trips(root)

        self.assertEqual(len(trips), 1)
        self.assertEqual(trips[0].zone_type, "x86_pkg_temp")
        self.assertEqual(trips[0].temperature_c, 100.0)
        self.assertIn("100.0 °C", format_kernel_trip_summary(trips))

    def test_summary_reports_multiple_exposed_trip_points(self) -> None:
        from sentinelux.protection import KernelCriticalTrip

        summary = format_kernel_trip_summary(
            (
                KernelCriticalTrip("thermal_zone0", "cpu", 100.0, 0),
                KernelCriticalTrip("thermal_zone1", "soc", 105.0, 1),
            )
        )
        self.assertIn("100.0 °C", summary)
        self.assertIn("2 soglie critiche esposte", summary)

    def test_missing_trip_is_reported_as_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            trips = read_kernel_critical_trips(Path(raw_root))
        self.assertEqual(trips, ())
        self.assertEqual(
            format_kernel_trip_summary(trips),
            "Non esposta dal kernel",
        )


class SleepActionTests(unittest.TestCase):
    def test_parses_logind_capability(self) -> None:
        class Result:
            returncode = 0
            stdout = 's "challenge"\n'

        with patch("sentinelux.protection.shutil.which", return_value="/usr/bin/busctl"):
            capability = sleep_action_capability(
                "hibernate",
                runner=lambda *args, **kwargs: Result(),
            )
        self.assertEqual(capability, "challenge")

    def test_requests_supported_action(self) -> None:
        calls: list[tuple[list[str], dict[str, object]]] = []

        def fake_popen(command: list[str], **kwargs: object) -> object:
            calls.append((command, kwargs))
            return object()

        with patch("sentinelux.protection.shutil.which", return_value="/usr/bin/systemctl"):
            request_sleep_action("hibernate", popen=fake_popen)

        self.assertEqual(calls[0][0], ["systemctl", "hibernate"])

    def test_rejects_unknown_action(self) -> None:
        with self.assertRaises(ValueError):
            request_sleep_action("reboot")


if __name__ == "__main__":
    unittest.main()
