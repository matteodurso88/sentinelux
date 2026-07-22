from __future__ import annotations

import unittest

from sentinelux.alerts import AlertKind, ThermalAlertController, ThermalState


class ThermalAlertControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = ThermalAlertController(
            warning_c=85,
            critical_c=95,
            hysteresis_c=5,
            reminder_seconds=300,
        )

    def test_enters_warning(self) -> None:
        event = self.controller.evaluate(86, 10)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.kind, AlertKind.WARNING)
        self.assertEqual(self.controller.state, ThermalState.WARNING)

    def test_enters_critical_directly(self) -> None:
        event = self.controller.evaluate(96, 10)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.kind, AlertKind.CRITICAL)
        self.assertEqual(self.controller.state, ThermalState.CRITICAL)

    def test_hysteresis_prevents_flapping(self) -> None:
        self.controller.evaluate(86, 10)
        self.assertIsNone(self.controller.evaluate(82, 20))
        self.assertEqual(self.controller.state, ThermalState.WARNING)
        event = self.controller.evaluate(79.9, 30)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.kind, AlertKind.RECOVERY)

    def test_reminder_is_throttled(self) -> None:
        self.controller.evaluate(86, 10)
        self.assertIsNone(self.controller.evaluate(87, 309))
        event = self.controller.evaluate(87, 310)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.kind, AlertKind.REMINDER)

    def test_critical_can_downgrade_to_warning(self) -> None:
        self.controller.evaluate(96, 10)
        event = self.controller.evaluate(89, 20)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.kind, AlertKind.WARNING)
        self.assertEqual(self.controller.state, ThermalState.WARNING)


if __name__ == "__main__":
    unittest.main()
