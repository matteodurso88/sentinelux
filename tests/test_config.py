from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sentinelux.config import AppConfig, load_config, save_config


class ConfigTests(unittest.TestCase):
    def test_alert_type_switches(self) -> None:
        config = AppConfig(alert_reminder_enabled=False)
        self.assertTrue(config.alert_enabled("warning"))
        self.assertFalse(config.alert_enabled("reminder"))
        self.assertFalse(config.alert_enabled("unknown"))

    def test_master_notification_switch_disables_all_alerts(self) -> None:
        config = AppConfig(notifications_enabled=False)
        self.assertFalse(config.alert_enabled("critical"))
        self.assertFalse(config.alert_enabled("recovery"))

    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            path = Path(raw_dir) / "config.json"
            expected = AppConfig(
                warning_temperature_c=80.0,
                critical_temperature_c=92.0,
                alert_recovery_enabled=False,
            )
            save_config(expected, path)
            loaded = load_config(path)
            self.assertEqual(loaded, expected)

    def test_old_config_receives_new_alert_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            path = Path(raw_dir) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "warning_temperature_c": 82.0,
                        "critical_temperature_c": 94.0,
                    }
                ),
                encoding="utf-8",
            )
            loaded = load_config(path)
            self.assertTrue(loaded.alert_warning_enabled)
            self.assertTrue(loaded.alert_critical_enabled)
            self.assertTrue(loaded.alert_reminder_enabled)
            self.assertTrue(loaded.alert_recovery_enabled)

    def test_invalid_threshold_order_is_rejected(self) -> None:
        config = AppConfig(warning_temperature_c=95.0, critical_temperature_c=90.0)
        with self.assertRaises(ValueError):
            config.validate()


if __name__ == "__main__":
    unittest.main()
