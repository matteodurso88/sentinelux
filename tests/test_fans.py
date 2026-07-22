from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sentinelux.fans import (
    FanManager,
    PRESET_LABELS,
    discover_fans,
    format_fan_channel,
    preset_pwm_value,
)


class FakeResult:
    returncode = 0
    stdout = ""
    stderr = ""


class FanDiscoveryTests(unittest.TestCase):
    def _tree(self, root: Path) -> Path:
        hwmon = root / "hwmon0"
        hwmon.mkdir()
        (hwmon / "name").write_text("testchip\n", encoding="utf-8")
        (hwmon / "fan1_label").write_text("CPU Fan\n", encoding="utf-8")
        (hwmon / "fan1_input").write_text("2400\n", encoding="utf-8")
        (hwmon / "pwm1").write_text("178\n", encoding="utf-8")
        (hwmon / "pwm1_enable").write_text("2\n", encoding="utf-8")
        return hwmon

    def test_discovers_controllable_channel(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._tree(root)
            channels = discover_fans(root)

        self.assertEqual(len(channels), 1)
        channel = channels[0]
        self.assertTrue(channel.controllable)
        self.assertEqual(channel.rpm, 2400)
        self.assertEqual(channel.enable_mode, 2)
        self.assertIn("CPU Fan", format_fan_channel(channel))
        self.assertIn("2400 RPM", format_fan_channel(channel))

    def test_preset_values_never_stop_the_fan(self) -> None:
        self.assertIsNone(preset_pwm_value("automatic"))
        self.assertGreaterEqual(preset_pwm_value("quiet") or 0, 128)
        self.assertEqual(preset_pwm_value("maximum"), 255)
        self.assertIn("performance", PRESET_LABELS)

    def test_manager_invokes_privileged_helper_with_validated_payload(self) -> None:
        calls: list[list[str]] = []

        def runner(command: list[str], **kwargs: object) -> FakeResult:
            calls.append(command)
            return FakeResult()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._tree(root)
            manager = FanManager(
                hwmon_root=root,
                runner=runner,
                sleeper=lambda _seconds: None,
                pkexec_path="/usr/bin/pkexec",
                helper_path=Path(__file__).parents[1]
                / "src"
                / "sentinelux"
                / "fan_helper.py",
                helper_trust_checker=lambda _path: True,
            )
            manager.apply_preset("quiet")
            self.assertEqual(manager.current_preset, "quiet")
            manager.restore_original()

        self.assertEqual(calls[0][2], "manual")
        manual_payload = json.loads(calls[0][3])
        self.assertEqual(manual_payload[0]["value"], preset_pwm_value("quiet"))
        self.assertEqual(calls[1][2], "restore")

    def test_read_only_fan_is_not_controllable(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            hwmon = root / "hwmon0"
            hwmon.mkdir()
            (hwmon / "name").write_text("readonly\n", encoding="utf-8")
            (hwmon / "fan1_input").write_text("1800\n", encoding="utf-8")
            channels = discover_fans(root)

        self.assertEqual(len(channels), 1)
        self.assertFalse(channels[0].controllable)


if __name__ == "__main__":
    unittest.main()
