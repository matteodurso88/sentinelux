"""Read-only Linux hwmon fan telemetry for the first public prerelease.

Fan/pwm sysfs attributes are observable but do not establish that firmware
permits user-space fan-speed control. This release never writes them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FanChannel:
    """One hwmon fan channel; multiple channels may report one physical fan."""

    identifier: str
    chip: str
    label: str
    index: int
    fan_input_path: Path | None
    pwm_path: Path | None
    enable_path: Path | None
    rpm: int | None
    pwm_value: int | None
    enable_mode: int | None

    @property
    def pwm_percent(self) -> float | None:
        if self.pwm_value is None:
            return None
        return self.pwm_value / 255.0 * 100.0

    @property
    def mode_label(self) -> str:
        if self.enable_mode is None:
            return "modo n.d."
        if self.enable_mode == 1:
            return "manuale (driver)"
        if self.enable_mode == 0:
            return "controllo disabilitato (driver)"
        return "automatico (driver)"


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _read_int(path: Path | None) -> int | None:
    if path is None:
        return None
    raw = _read_text(path)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _channel_indices(directory: Path) -> tuple[int, ...]:
    indices: set[int] = set()
    for path in directory.glob("fan*_input"):
        match = re.fullmatch(r"fan(\d+)_input", path.name)
        if match:
            indices.add(int(match.group(1)))
    for path in directory.glob("pwm[0-9]*"):
        match = re.fullmatch(r"pwm(\d+)", path.name)
        if match:
            indices.add(int(match.group(1)))
    return tuple(sorted(indices))


def discover_fans(
    hwmon_root: Path = Path("/sys/class/hwmon"),
) -> tuple[FanChannel, ...]:
    """Read hwmon fan telemetry; never open PWM or mode paths for writing."""

    channels: list[FanChannel] = []
    for directory in sorted(hwmon_root.glob("hwmon*"), key=lambda path: path.name):
        chip = _read_text(directory / "name") or directory.name
        for index in _channel_indices(directory):
            fan_input = directory / f"fan{index}_input"
            pwm = directory / f"pwm{index}"
            enable = directory / f"pwm{index}_enable"
            fan_input_path = fan_input if fan_input.exists() else None
            pwm_path = pwm if pwm.exists() else None
            enable_path = enable if enable.exists() else None
            if fan_input_path is None and pwm_path is None:
                continue
            label = _read_text(directory / f"fan{index}_label") or f"Ventola {index}"
            channels.append(
                FanChannel(
                    identifier=f"{directory.name}:fan{index}",
                    chip=chip,
                    label=label,
                    index=index,
                    fan_input_path=fan_input_path,
                    pwm_path=pwm_path,
                    enable_path=enable_path,
                    rpm=_read_int(fan_input_path),
                    pwm_value=_read_int(pwm_path),
                    enable_mode=_read_int(enable_path),
                )
            )
    return tuple(channels)


def format_fan_channel(channel: FanChannel) -> str:
    rpm = f"{channel.rpm} RPM" if channel.rpm is not None else "RPM n.d."
    if channel.pwm_percent is None:
        pwm = "PWM n.d."
    else:
        pwm = f"PWM {channel.pwm_percent:.0f}% (driver)"
    return f"{channel.label} · {rpm} · {pwm} · {channel.mode_label}"


class FanManager:
    """Read-only live fan discovery; no privileged-control implementation."""

    def __init__(
        self, *, hwmon_root: Path = Path("/sys/class/hwmon")
    ) -> None:
        self.hwmon_root = hwmon_root
        self._channels: tuple[FanChannel, ...] = ()
        self.refresh()

    @property
    def channels(self) -> tuple[FanChannel, ...]:
        return self._channels

    def refresh(self) -> tuple[FanChannel, ...]:
        self._channels = discover_fans(self.hwmon_root)
        return self._channels
