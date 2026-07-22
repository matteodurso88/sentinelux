"""Thermal protection, kernel trip-point discovery, and sleep actions."""

from __future__ import annotations

import glob
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class KernelCriticalTrip:
    """A read-only critical trip point exposed by the Linux thermal core."""

    zone: str
    zone_type: str
    temperature_c: float
    trip_index: int


class ProtectionEventKind(str, Enum):
    ARMED = "armed"
    CANCELLED = "cancelled"
    TRIGGERED = "triggered"


@dataclass(frozen=True, slots=True)
class ProtectionEvent:
    kind: ProtectionEventKind
    temperature_c: float
    action: str
    persistence_seconds: float


class ThermalProtectionController:
    """Require a sustained over-temperature condition before a sleep action."""

    def __init__(
        self,
        *,
        enabled: bool,
        threshold_c: float,
        persistence_seconds: float,
        recovery_hysteresis_c: float,
        action: str,
    ) -> None:
        self.enabled = enabled
        self.threshold_c = threshold_c
        self.persistence_seconds = persistence_seconds
        self.recovery_hysteresis_c = recovery_hysteresis_c
        self.action = action
        self.over_threshold_since: float | None = None
        self.triggered = False

    def evaluate(
        self,
        temperature_c: float | None,
        now: float,
    ) -> ProtectionEvent | None:
        if not self.enabled or temperature_c is None:
            self.reset()
            return None

        if temperature_c >= self.threshold_c:
            if self.triggered:
                return None
            if self.over_threshold_since is None:
                self.over_threshold_since = now
                return ProtectionEvent(
                    ProtectionEventKind.ARMED,
                    temperature_c,
                    self.action,
                    self.persistence_seconds,
                )
            if now - self.over_threshold_since >= self.persistence_seconds:
                self.triggered = True
                return ProtectionEvent(
                    ProtectionEventKind.TRIGGERED,
                    temperature_c,
                    self.action,
                    self.persistence_seconds,
                )
            return None

        recovery_limit = self.threshold_c - self.recovery_hysteresis_c
        if self.over_threshold_since is not None and temperature_c <= recovery_limit:
            self.over_threshold_since = None
            self.triggered = False
            return ProtectionEvent(
                ProtectionEventKind.CANCELLED,
                temperature_c,
                self.action,
                self.persistence_seconds,
            )
        return None

    def reset(self) -> None:
        self.over_threshold_since = None
        self.triggered = False


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _read_millidegrees(path: Path) -> float | None:
    raw = _read_text(path)
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if abs(value) > 1000:
        value /= 1000.0
    if not -20.0 <= value <= 150.0:
        return None
    return value


def read_kernel_critical_trips(
    thermal_root: Path = Path("/sys/class/thermal"),
) -> tuple[KernelCriticalTrip, ...]:
    """Read critical thermal-zone trip points without modifying sysfs."""

    trips: list[KernelCriticalTrip] = []
    for raw_zone in glob.glob(str(thermal_root / "thermal_zone*")):
        zone_path = Path(raw_zone)
        zone_type = _read_text(zone_path / "type") or zone_path.name
        for type_path in zone_path.glob("trip_point_*_type"):
            match = re.fullmatch(r"trip_point_(\d+)_type", type_path.name)
            if match is None:
                continue
            trip_type = (_read_text(type_path) or "").strip().lower()
            if trip_type != "critical":
                continue
            index = int(match.group(1))
            temperature = _read_millidegrees(
                zone_path / f"trip_point_{index}_temp"
            )
            if temperature is None:
                continue
            trips.append(
                KernelCriticalTrip(
                    zone=zone_path.name,
                    zone_type=zone_type,
                    temperature_c=temperature,
                    trip_index=index,
                )
            )
    return tuple(sorted(trips, key=lambda trip: (trip.temperature_c, trip.zone)))


def lowest_kernel_critical_trip(
    thermal_root: Path = Path("/sys/class/thermal"),
) -> KernelCriticalTrip | None:
    trips = read_kernel_critical_trips(thermal_root)
    return trips[0] if trips else None


def _parse_busctl_capability(output: str) -> str:
    match = re.search(r'"(yes|no|challenge|na)"', output)
    return match.group(1) if match else "unknown"


def sleep_action_capability(
    action: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    """Return yes, challenge, no, na, or unknown for a logind sleep action."""

    methods = {
        "hibernate": "CanHibernate",
        "suspend": "CanSuspend",
    }
    method = methods.get(action)
    if method is None or shutil.which("busctl") is None:
        return "unknown"
    try:
        result = runner(
            [
                "busctl",
                "call",
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager",
                method,
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    return _parse_busctl_capability(result.stdout)


def request_sleep_action(
    action: str,
    popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> None:
    """Ask systemd-logind to suspend or hibernate the machine."""

    if action not in {"hibernate", "suspend"}:
        raise ValueError(f"unsupported thermal action: {action}")
    if shutil.which("systemctl") is None:
        raise RuntimeError("systemctl is not available")
    try:
        popen(
            ["systemctl", action],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        raise RuntimeError(f"cannot request {action}: {exc}") from exc


def format_kernel_trip_summary(
    trips: Sequence[KernelCriticalTrip],
) -> str:
    if not trips:
        return "Non esposta dal kernel"
    lowest = min(trips, key=lambda trip: trip.temperature_c)
    summary = f"{lowest.temperature_c:.1f} °C · {lowest.zone_type} ({lowest.zone})"
    if len(trips) > 1:
        summary += f" · {len(trips)} soglie critiche esposte"
    return summary
