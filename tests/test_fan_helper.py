"""Tests for the narrowly scoped privileged thermal-profile writer."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sentinelux import fan_helper


class PlatformProfileHelperTests(unittest.TestCase):
    def test_allows_only_kernel_advertised_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile = root / "platform_profile"
            choices = root / "platform_profile_choices"
            profile.write_text("balanced", encoding="ascii")
            choices.write_text("cool quiet balanced performance", encoding="ascii")

            with patch.object(fan_helper, "PROFILE_PATH", profile), patch.object(
                fan_helper, "PROFILE_CHOICES_PATH", choices
            ):
                fan_helper.apply_operation("profile", [{"profile": "quiet"}])
                self.assertEqual(profile.read_text().strip(), "quiet")

                for payload in (
                    [{"profile": "maximum"}],
                    [{"profile": "custom"}],
                    [{"profile": "../../etc/shadow"}],
                    [{"profile": "quiet", "path": "/etc/shadow"}],
                    [{"profile": 2}],
                    [],
                    [{"profile": "cool"}, {"profile": "quiet"}],
                ):
                    with self.subTest(payload=payload):
                        with self.assertRaises(fan_helper.HelperError):
                            fan_helper.apply_operation("profile", payload)
                        self.assertEqual(profile.read_text().strip(), "quiet")

                choices.write_text("balanced performance", encoding="ascii")
                with self.assertRaisesRegex(fan_helper.HelperError, "non supportato"):
                    fan_helper.apply_operation("profile", [{"profile": "cool"}])
                self.assertEqual(profile.read_text().strip(), "quiet")

    def test_absent_profile_interface_rejects_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(fan_helper, "PROFILE_PATH", root / "missing"), patch.object(
                fan_helper, "PROFILE_CHOICES_PATH", root / "missing-choices"
            ):
                with self.assertRaises(fan_helper.HelperError):
                    fan_helper.apply_operation("profile", [{"profile": "balanced"}])


if __name__ == "__main__":
    unittest.main()
