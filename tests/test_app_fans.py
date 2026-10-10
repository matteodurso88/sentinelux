"""Regression for preservation of session-scoped fan control on config save."""

from __future__ import annotations

import unittest

from sentinelux.app import SentineluxApplication
from sentinelux.config import AppConfig


class FanLifecycleTests(unittest.TestCase):
    def test_app_keeps_fan_manager_and_its_baseline_after_save(self) -> None:
        app = SentineluxApplication.__new__(SentineluxApplication)
        original_manager = object()
        app.fans = original_manager
        app.config = AppConfig()
        app.running = False
        app._new_alert_controller = lambda _config: object()
        app._new_protection_controller = lambda _config: object()
        app._sync_notification_controls = lambda: None
        app._refresh = lambda: True

        app._apply_config(AppConfig())

        self.assertIs(app.fans, original_manager)


if __name__ == "__main__":
    unittest.main()
