from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sentinelux.fans import (
    FanControlError,
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
            operation = command[2]
            for entry in json.loads(command[3]):
                Path(entry["pwm"]).write_text(str(entry["value"]), encoding="utf-8")
                Path(entry["enable"]).write_text(
                    str(entry.get("enable_mode", 1 if operation == "manual" else 2)),
                    encoding="utf-8",
                )
            return FakeResult()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._tree(root)
            manager = FanManager(
                hwmon_root=root,
                platform_root=root,
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
            self.assertIn("RPM sostanzialmente invariati", manager.last_feedback)
            manager.restore_original()

        self.assertEqual(calls[0][2], "manual")
        manual_payload = json.loads(calls[0][3])
        self.assertEqual(manual_payload[0]["value"], preset_pwm_value("quiet"))
        self.assertEqual(calls[1][2], "restore")

    def test_rejects_ignored_pwm_commands_and_restores_baseline(self) -> None:
        calls: list[list[str]] = []

        def ignored_runner(command: list[str], **kwargs: object) -> FakeResult:
            calls.append(command)
            return FakeResult()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            hwmon = self._tree(root)
            manager = FanManager(
                hwmon_root=root,
                platform_root=root,
                runner=ignored_runner,
                sleeper=lambda _seconds: None,
                pkexec_path="/usr/bin/pkexec",
                helper_trust_checker=lambda _path: True,
            )
            with self.assertRaisesRegex(FanControlError, "driver/firmware"):
                manager.apply_preset("maximum")
            self.assertEqual(manager.current_preset, "automatic")
            self.assertEqual((hwmon / "pwm1").read_text().strip(), "178")
        self.assertEqual([call[2] for call in calls], ["manual", "restore"])

    def test_stalled_rpm_restores_original_mode(self) -> None:
        calls: list[str] = []

        def simulated_runner(command: list[str], **kwargs: object) -> FakeResult:
            operation = command[2]
            calls.append(operation)
            for entry in json.loads(command[3]):
                Path(entry["pwm"]).write_text(str(entry["value"]), encoding="utf-8")
                Path(entry["enable"]).write_text(
                    str(entry.get("enable_mode", 1)),
                    encoding="utf-8",
                )
                if operation == "manual":
                    Path(entry["pwm"]).with_name("fan1_input").write_text(
                        "0", encoding="utf-8"
                    )
            return FakeResult()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            hwmon = self._tree(root)
            manager = FanManager(
                hwmon_root=root,
                platform_root=root,
                runner=simulated_runner,
                sleeper=lambda _seconds: None,
                pkexec_path="/usr/bin/pkexec",
                helper_trust_checker=lambda _path: True,
            )
            with self.assertRaisesRegex(FanControlError, "RPM nullo"):
                manager.apply_preset("quiet")
            self.assertEqual(manager.current_preset, "automatic")
            self.assertEqual((hwmon / "pwm1_enable").read_text().strip(), "2")
        self.assertEqual(calls, ["manual", "restore"])

    def test_native_profile_takes_priority_over_generic_pwm(self) -> None:
        calls: list[str] = []

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._tree(root)
            (root / "platform_profile").write_text("balanced", encoding="ascii")
            (root / "platform_profile_choices").write_text(
                "cool quiet balanced performance", encoding="ascii"
            )

            def runner(command: list[str], **kwargs: object) -> FakeResult:
                calls.append(command[2])
                if command[2] == "profile":
                    new_profile = json.loads(command[3])[0]["profile"]
                    (root / "platform_profile").write_text(new_profile, encoding="ascii")
                return FakeResult()

            manager = FanManager(
                hwmon_root=root,
                platform_root=root,
                runner=runner,
                sleeper=lambda _seconds: None,
                pkexec_path="/usr/bin/pkexec",
                helper_trust_checker=lambda _path: True,
            )
            self.assertEqual(manager.control_backend, "platform")
            self.assertEqual(
                tuple(key for key, _label in manager.preset_options),
                ("automatic", "quiet", "balanced", "performance", "cool"),
            )
            manager.apply_preset("cool")
            self.assertEqual(manager.current_preset, "cool")
            self.assertEqual(manager.current_platform_profile, "cool")
            self.assertIn("politica termica", manager.last_feedback)
            self.assertEqual((root / "hwmon0" / "pwm1").read_text().strip(), "178")

            manager.restore_original()
            self.assertEqual(manager.current_platform_profile, "balanced")
            self.assertEqual(manager.current_preset, "automatic")

        self.assertEqual(calls, ["profile", "profile"])

    def test_native_profile_rejects_unsupported_preset(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._tree(root)
            (root / "platform_profile").write_text("balanced", encoding="ascii")
            (root / "platform_profile_choices").write_text(
                "quiet balanced", encoding="ascii"
            )
            manager = FanManager(
                hwmon_root=root,
                platform_root=root,
                pkexec_path="/usr/bin/pkexec",
                helper_trust_checker=lambda _path: True,
            )
            with self.assertRaisesRegex(FanControlError, "non disponibile"):
                manager.apply_preset("maximum")
            self.assertEqual(manager.current_platform_profile, "balanced")

    def test_native_profile_detects_firmware_override(self) -> None:
        calls: list[str] = []

        def ignored(command: list[str], **kwargs: object) -> FakeResult:
            calls.append(command[2])
            return FakeResult()

        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._tree(root)
            (root / "platform_profile").write_text("balanced", encoding="ascii")
            (root / "platform_profile_choices").write_text(
                "quiet balanced performance", encoding="ascii"
            )
            manager = FanManager(
                hwmon_root=root,
                platform_root=root,
                runner=ignored,
                sleeper=lambda _seconds: None,
                pkexec_path="/usr/bin/pkexec",
                helper_trust_checker=lambda _path: True,
            )
            with self.assertRaisesRegex(FanControlError, "non ha mantenuto"):
                manager.apply_preset("performance")
            self.assertEqual(manager.current_preset, "automatic")
            self.assertEqual(manager.current_platform_profile, "balanced")
        self.assertEqual(calls, ["profile", "profile"])

    def test_dell_smm_only_is_not_generic_pwm_backend(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            hwmon = self._tree(root)
            (hwmon / "name").write_text("dell_smm", encoding="ascii")
            manager = FanManager(
                hwmon_root=root,
                platform_root=root,
                pkexec_path="/usr/bin/pkexec",
                helper_trust_checker=lambda _path: True,
            )
            self.assertEqual(len(manager.channels), 1)
            self.assertEqual(manager.controllable_channels, ())
            self.assertIsNone(manager.control_backend)
            self.assertFalse(manager.control_available)

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
