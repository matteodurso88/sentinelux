from __future__ import annotations

import unittest

from sentinelux.config import AppConfig


class ProtectionConfigTests(unittest.TestCase):
    def test_default_protection_is_disabled(self) -> None:
        config = AppConfig()
        config.validate()
        self.assertFalse(config.thermal_protection_enabled)
        self.assertEqual(config.thermal_protection_action, "hibernate")

    def test_enabled_action_threshold_cannot_be_below_critical_alert(self) -> None:
        config = AppConfig(
            thermal_protection_enabled=True,
            thermal_protection_temperature_c=94.0,
        )
        with self.assertRaises(ValueError):
            config.validate()

    def test_disabled_protection_does_not_constrain_alert_threshold(self) -> None:
        config = AppConfig(
            critical_temperature_c=100.0,
            thermal_protection_enabled=False,
            thermal_protection_temperature_c=97.0,
        )
        config.validate()

    def test_action_must_be_supported(self) -> None:
        config = AppConfig(thermal_protection_action="poweroff")
        with self.assertRaises(ValueError):
            config.validate()


if __name__ == "__main__":
    unittest.main()
