"""Configuration loading for Sentinelux."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AppConfig:
    """Runtime configuration persisted as JSON."""

    refresh_interval_seconds: float = 2.0
    warning_temperature_c: float = 85.0
    critical_temperature_c: float = 95.0
    recovery_hysteresis_c: float = 5.0
    reminder_interval_seconds: float = 300.0
    notifications_enabled: bool = True
    alert_warning_enabled: bool = True
    alert_critical_enabled: bool = True
    alert_reminder_enabled: bool = True
    alert_recovery_enabled: bool = True
    thermal_protection_enabled: bool = False
    thermal_protection_action: str = "hibernate"
    thermal_protection_temperature_c: float = 97.0
    thermal_protection_persistence_seconds: float = 20.0
    thermal_protection_recovery_hysteresis_c: float = 3.0

    def validate(self) -> None:
        if self.refresh_interval_seconds < 0.5:
            raise ValueError("refresh_interval_seconds must be at least 0.5")
        if self.warning_temperature_c <= 0:
            raise ValueError("warning_temperature_c must be positive")
        if self.critical_temperature_c <= self.warning_temperature_c:
            raise ValueError(
                "critical_temperature_c must be greater than warning_temperature_c"
            )
        if self.recovery_hysteresis_c < 0:
            raise ValueError("recovery_hysteresis_c cannot be negative")
        if self.reminder_interval_seconds < 30:
            raise ValueError("reminder_interval_seconds must be at least 30")
        if self.thermal_protection_action not in {"hibernate", "suspend"}:
            raise ValueError(
                "thermal_protection_action must be hibernate or suspend"
            )
        if (
            self.thermal_protection_enabled
            and self.thermal_protection_temperature_c < self.critical_temperature_c
        ):
            raise ValueError(
                "thermal_protection_temperature_c must be at least the critical alert threshold"
            )
        if self.thermal_protection_persistence_seconds < 5:
            raise ValueError(
                "thermal_protection_persistence_seconds must be at least 5"
            )
        if self.thermal_protection_recovery_hysteresis_c < 0:
            raise ValueError(
                "thermal_protection_recovery_hysteresis_c cannot be negative"
            )

        boolean_fields = (
            "notifications_enabled",
            "alert_warning_enabled",
            "alert_critical_enabled",
            "alert_reminder_enabled",
            "alert_recovery_enabled",
            "thermal_protection_enabled",
        )
        for field_name in boolean_fields:
            if not isinstance(getattr(self, field_name), bool):
                raise ValueError(f"{field_name} must be a boolean")

    def alert_enabled(self, alert_kind: str) -> bool:
        mapping = {
            "warning": self.alert_warning_enabled,
            "critical": self.alert_critical_enabled,
            "reminder": self.alert_reminder_enabled,
            "recovery": self.alert_recovery_enabled,
        }
        return self.notifications_enabled and mapping.get(alert_kind, False)


def config_path() -> Path:
    """Return the XDG-compliant Sentinelux configuration path."""

    root = Path(
        os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    )
    return root / "sentinelux" / "config.json"


def _merge_config(raw: dict[str, Any]) -> AppConfig:
    allowed = set(AppConfig.__dataclass_fields__)
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ValueError(f"unknown configuration keys: {', '.join(unknown)}")

    config = AppConfig(**raw)
    config.validate()
    return config


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    """Write configuration atomically and return its path."""

    config.validate()
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(asdict(config), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target


def load_config(path: Path | None = None, create: bool = True) -> AppConfig:
    """Load configuration, optionally creating defaults on first run."""

    target = path or config_path()
    if not target.exists():
        config = AppConfig()
        config.validate()
        if create:
            save_config(config, target)
        return config

    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {target}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"configuration root in {target} must be a JSON object")

    return _merge_config(raw)
