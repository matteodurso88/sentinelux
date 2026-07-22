"""Thermal alert state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ThermalState(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertKind(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"
    REMINDER = "reminder"
    RECOVERY = "recovery"


@dataclass(frozen=True, slots=True)
class AlertEvent:
    kind: AlertKind
    temperature_c: float
    previous_state: ThermalState
    current_state: ThermalState


class ThermalAlertController:
    """Track thermal state with hysteresis and reminder throttling."""

    def __init__(
        self,
        warning_c: float,
        critical_c: float,
        hysteresis_c: float,
        reminder_seconds: float,
    ) -> None:
        if critical_c <= warning_c:
            raise ValueError("critical threshold must exceed warning threshold")
        if hysteresis_c < 0:
            raise ValueError("hysteresis cannot be negative")
        if reminder_seconds <= 0:
            raise ValueError("reminder interval must be positive")

        self.warning_c = warning_c
        self.critical_c = critical_c
        self.hysteresis_c = hysteresis_c
        self.reminder_seconds = reminder_seconds
        self.state = ThermalState.NORMAL
        self.last_notification_monotonic: float | None = None

    def reset(self) -> None:
        self.state = ThermalState.NORMAL
        self.last_notification_monotonic = None

    def _next_state(self, temperature_c: float) -> ThermalState:
        if self.state is ThermalState.NORMAL:
            if temperature_c >= self.critical_c:
                return ThermalState.CRITICAL
            if temperature_c >= self.warning_c:
                return ThermalState.WARNING
            return ThermalState.NORMAL

        if self.state is ThermalState.WARNING:
            if temperature_c >= self.critical_c:
                return ThermalState.CRITICAL
            if temperature_c < self.warning_c - self.hysteresis_c:
                return ThermalState.NORMAL
            return ThermalState.WARNING

        if temperature_c < self.warning_c - self.hysteresis_c:
            return ThermalState.NORMAL
        if temperature_c < self.critical_c - self.hysteresis_c:
            return ThermalState.WARNING
        return ThermalState.CRITICAL

    def evaluate(
        self, temperature_c: float | None, now_monotonic: float
    ) -> AlertEvent | None:
        """Evaluate a sample and return a notification-worthy event."""

        if temperature_c is None:
            return None

        previous = self.state
        current = self._next_state(temperature_c)
        self.state = current

        if current is not previous:
            if current is ThermalState.CRITICAL:
                kind = AlertKind.CRITICAL
            elif current is ThermalState.WARNING:
                kind = AlertKind.WARNING
            else:
                kind = AlertKind.RECOVERY

            self.last_notification_monotonic = now_monotonic
            return AlertEvent(kind, temperature_c, previous, current)

        if current is not ThermalState.NORMAL:
            last = self.last_notification_monotonic
            if last is None or now_monotonic - last >= self.reminder_seconds:
                self.last_notification_monotonic = now_monotonic
                return AlertEvent(
                    AlertKind.REMINDER,
                    temperature_c,
                    previous,
                    current,
                )

        return None
