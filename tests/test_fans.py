"""Read-only fan telemetry regressions for the public alpha release."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sentinelux.fans import FanManager, discover_fans, format_fan_channel


class FanTelemetryTests(unittest.TestCase):
    def _tree(self, root: Path) -> Path:
        hwmon = root / "hwmon0"
        hwmon.mkdir()
        (hwmon / "name").write_text("dell_smm\n", encoding="utf-8")
        (hwmon / "fan1_label").write_text("CPU Fan\n", encoding="utf-8")
        (hwmon / "fan1_input").write_text("1406\n", encoding="utf-8")
        (hwmon / "pwm1").write_text("128\n", encoding="utf-8")
        (hwmon / "pwm1_enable").write_text("1\n", encoding="utf-8")
        return hwmon

    def test_hwmon_snapshot_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            chip = self._tree(root)
            before = {
                name: (chip / name).read_bytes()
                for name in ("fan1_input", "pwm1", "pwm1_enable")
            }
            manager = FanManager(hwmon_root=root)
            self.assertEqual(len(manager.channels), 1)
            self.assertEqual(manager.channels[0].rpm, 1406)
            self.assertEqual(manager.channels[0].pwm_value, 128)
            self.assertEqual(manager.channels[0].enable_mode, 1)
            self.assertIn("1406 RPM", format_fan_channel(manager.channels[0]))
            self.assertIn("(driver)", format_fan_channel(manager.channels[0]))
            manager.refresh()
            after = {name: (chip / name).read_bytes() for name in before}
            self.assertEqual(before, after)

            # Even a chip advertising writable-looking PWM has no control API
            # in this prerelease. No privileged runner or helper is needed.
            self.assertFalse(hasattr(manager, "apply_preset"))
            self.assertFalse(hasattr(manager, "_run_helper"))
            self.assertFalse(hasattr(manager, "restore_original"))

    def test_supports_missing_channels_and_read_only_tachometer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(discover_fans(root), ())
            chip = root / "hwmon0"
            chip.mkdir()
            (chip / "name").write_text("dell_ddv", encoding="utf-8")
            (chip / "fan1_input").write_text("1406", encoding="utf-8")
            channel, = discover_fans(root)
            self.assertEqual(channel.rpm, 1406)
            self.assertIsNone(channel.pwm_value)
            self.assertIsNone(channel.enable_mode)
            self.assertIn("PWM n.d.", format_fan_channel(channel))

    def test_duplicates_are_reported_as_channels_not_physical_fan_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self._tree(root)
            second = root / "hwmon1"
            second.mkdir()
            (second / "name").write_text("dell_ddv", encoding="utf-8")
            (second / "fan1_input").write_text("1406", encoding="utf-8")
            found = discover_fans(root)
            self.assertEqual(len(found), 2)
            self.assertEqual({c.chip for c in found}, {"dell_smm", "dell_ddv"})
            self.assertEqual({c.rpm for c in found}, {1406})
            self.assertEqual(found[0].identifier, "hwmon0:fan1")
            self.assertEqual(found[1].identifier, "hwmon1:fan1")
            self.assertEqual((first / "pwm1").read_text(), "128\n")


if __name__ == "__main__":
    unittest.main()
