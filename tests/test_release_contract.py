"""Release safety and version identity contract for the first public alpha."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import sentinelux
from sentinelux.fans import FanManager


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class FirstAlphaContractTests(unittest.TestCase):
    def test_version_matches_python_release_candidate(self) -> None:
        self.assertEqual(sentinelux.__version__, "0.1.0a1")
        manifest = (REPOSITORY_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        match = re.search(r'^version\s*=\s*"([^"]+)"', manifest, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), sentinelux.__version__)

    def test_experimental_privileged_fan_control_is_not_distributed(self) -> None:
        self.assertFalse(
            (REPOSITORY_ROOT / "src" / "sentinelux" / "fan_helper.py").exists()
        )
        self.assertFalse(
            (REPOSITORY_ROOT / "scripts" / "install-fan-helper.sh").exists()
        )
        for name in ("apply_preset", "_run_helper", "restore_original"):
            self.assertFalse(hasattr(FanManager, name))

    def test_fan_preferences_have_no_apply_preset_controls(self) -> None:
        source = (
            REPOSITORY_ROOT / "src" / "sentinelux" / "settings.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("fan_apply_button", source)
        self.assertNotIn("fan_preset_combo", source)
        self.assertNotIn("_apply_fan_preset", source)
        self.assertIn("monitoraggio in sola lettura", source)


if __name__ == "__main__":
    unittest.main()
