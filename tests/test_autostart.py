from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sentinelux.autostart import (
    AutostartError,
    autostart_path,
    is_autostart_enabled,
    set_autostart_enabled,
)


class AutostartTests(unittest.TestCase):
    def _launcher(self, root: Path) -> Path:
        launcher = root / "sentinelux launcher"
        launcher.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        launcher.chmod(0o755)
        return launcher

    def test_enable_and_disable_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            target = root / "autostart" / "io.matt88.Sentinelux.desktop"
            launcher = self._launcher(root)

            set_autostart_enabled(True, path=target, executable=launcher)
            self.assertTrue(is_autostart_enabled(target))
            content = target.read_text(encoding="utf-8")
            self.assertIn(f'Exec="{launcher}"', content)
            self.assertIn("X-GNOME-Autostart-enabled=true", content)

            set_autostart_enabled(False, path=target)
            self.assertFalse(is_autostart_enabled(target))

    def test_uses_xdg_config_home(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": raw_dir}, clear=False):
                self.assertEqual(
                    autostart_path(),
                    Path(raw_dir) / "autostart" / "io.matt88.Sentinelux.desktop",
                )

    def test_rejects_non_executable_launcher(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            launcher = root / "sentinelux"
            launcher.write_text("not executable\n", encoding="utf-8")
            with self.assertRaises(AutostartError):
                set_autostart_enabled(
                    True,
                    path=root / "entry.desktop",
                    executable=launcher,
                )


if __name__ == "__main__":
    unittest.main()
