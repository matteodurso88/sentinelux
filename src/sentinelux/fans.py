"""Safe Linux hwmon fan discovery and session-scoped preset control."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


PRESET_PERCENTAGES: dict[str, int | None] = {
    "automatic": None,
    "quiet": 55,
    "balanced": 70,
    "performance": 85,
    "maximum": 100,
}

PRESET_LABELS: dict[str, str] = {
    "automatic": "Automatico",
    "quiet": "Silenzioso · 55%",
    "balanced": "Bilanciato · 70%",
    "performance": "Prestazioni · 85%",
    "maximum": "Massimo · 100%",
}


class FanControlError(RuntimeError):
    """Raised when a fan preset cannot be applied safely."""


@dataclass(frozen=True, slots=True)
class FanChannel:
    """One fan/PWM channel exported by a Linux hwmon device."""

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
    def controllable(self) -> bool:
        """Require tachometer feedback and readable PWM/mode state."""

        return (
            self.fan_input_path is not None
            and self.pwm_path is not None
            and self.enable_path is not None
            and self.rpm is not None
            and self.pwm_value is not None
            and self.enable_mode is not None
        )

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
            return "manuale"
        if self.enable_mode == 0:
            return "controllo disabilitato"
        return "automatico"


@dataclass(frozen=True, slots=True)
class FanState:
    pwm_value: int
    enable_mode: int


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
    """Discover RPM and PWM channels exposed through the standard hwmon ABI."""

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
            label = (
                _read_text(directory / f"fan{index}_label")
                or f"Ventola {index}"
            )
            if fan_input_path is None and pwm_path is None:
                continue
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


def preset_pwm_value(preset: str) -> int | None:
    if preset not in PRESET_PERCENTAGES:
        raise ValueError(f"unknown fan preset: {preset}")
    percentage = PRESET_PERCENTAGES[preset]
    if percentage is None:
        return None
    return round(255 * percentage / 100)


def format_fan_channel(channel: FanChannel) -> str:
    rpm = f"{channel.rpm} RPM" if channel.rpm is not None else "RPM n.d."
    if channel.pwm_percent is None:
        pwm = "PWM n.d."
    else:
        pwm = f"PWM {channel.pwm_percent:.0f}%"
    return f"{channel.label} · {rpm} · {pwm} · {channel.mode_label}"


class FanManager:
    """Apply conservative fan presets for the current Sentinelux session only."""

    def __init__(
        self,
        *,
        hwmon_root: Path = Path("/sys/class/hwmon"),
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        sleeper: Callable[[float], None] = time.sleep,
        pkexec_path: str | None = None,
        helper_path: Path | None = None,
        helper_trust_checker: Callable[[Path], bool] | None = None,
    ) -> None:
        self.hwmon_root = hwmon_root
        self.runner = runner
        self.sleeper = sleeper
        self.pkexec_path = pkexec_path
        self.helper_path = helper_path or Path("/usr/libexec/sentinelux-fan-helper")
        self.helper_trust_checker = helper_trust_checker or self._helper_is_trusted
        self.current_preset = "automatic"
        self.last_feedback = ""
        self._channels: tuple[FanChannel, ...] = ()
        self._baseline: dict[str, FanState] = {}
        self.refresh()

    @property
    def channels(self) -> tuple[FanChannel, ...]:
        return self._channels

    @property
    def controllable_channels(self) -> tuple[FanChannel, ...]:
        return tuple(channel for channel in self._channels if channel.controllable)

    @property
    def helper_ready(self) -> bool:
        return (
            self._pkexec() is not None
            and self.helper_trust_checker(self.helper_path)
        )

    @property
    def control_available(self) -> bool:
        return bool(self.controllable_channels) and self.helper_ready

    @staticmethod
    def _helper_is_trusted(path: Path) -> bool:
        try:
            stat = path.stat()
        except OSError:
            return False
        return path.is_file() and stat.st_uid == 0 and not (stat.st_mode & 0o022)

    def _pkexec(self) -> str | None:
        return self.pkexec_path or shutil.which("pkexec")

    def refresh(self) -> tuple[FanChannel, ...]:
        self._channels = discover_fans(self.hwmon_root)
        for channel in self._channels:
            if (
                channel.controllable
                and channel.identifier not in self._baseline
                and channel.pwm_value is not None
                and channel.enable_mode is not None
            ):
                self._baseline[channel.identifier] = FanState(
                    pwm_value=channel.pwm_value,
                    enable_mode=channel.enable_mode,
                )
        return self._channels

    def apply_preset(self, preset: str) -> None:
        value = preset_pwm_value(preset)
        self.refresh()
        channels = self.controllable_channels
        if not channels:
            raise FanControlError(
                "nessun canale PWM con feedback RPM e stato leggibile è disponibile"
            )

        if preset == "automatic":
            payload = []
            for channel in channels:
                baseline = self._baseline[channel.identifier]
                automatic_mode = (
                    baseline.enable_mode if baseline.enable_mode >= 2 else 2
                )
                payload.append(
                    {
                        "pwm": str(channel.pwm_path),
                        "enable": str(channel.enable_path),
                        "value": baseline.pwm_value,
                        "enable_mode": automatic_mode,
                    }
                )
            self._run_helper("automatic", payload)
            self.current_preset = preset
            self.last_feedback = "Controllo automatico richiesto al driver."
            self.refresh()
            return

        assert value is not None
        payload = [
            {
                "pwm": str(channel.pwm_path),
                "enable": str(channel.enable_path),
                "value": value,
            }
            for channel in channels
        ]
        self.last_feedback = ""
        self._run_helper("manual", payload)
        self.current_preset = preset
        self.sleeper(1.1)
        updated = {channel.identifier: channel for channel in self.refresh()}

        # A successful privileged helper exit does not prove that the kernel
        # accepted the requested PWM/mode, much less that the fan responded.
        invalid = [
            channel.label
            for channel in channels
            if (
                (observed := updated.get(channel.identifier)) is None
                or observed.pwm_value != value
                or observed.enable_mode != 1
            )
        ]
        stalled = [
            channel.label
            for channel in channels
            if updated.get(channel.identifier) is not None
            and updated[channel.identifier].rpm == 0
        ]
        if invalid or stalled:
            failure = (
                "Il driver/firmware non ha mantenuto PWM e modo manuale: "
                + ", ".join(invalid)
                if invalid
                else "Feedback RPM nullo dopo l'applicazione: " + ", ".join(stalled)
            )
            try:
                self.restore_original()
            except FanControlError as restore_error:
                raise FanControlError(
                    f"{failure}. Ripristino non riuscito: {restore_error}"
                ) from restore_error
            raise FanControlError(f"{failure}. Controllo automatico ripristinato.")

        rpm_changes = [
            channel
            for channel in channels
            if (
                updated[channel.identifier].rpm is not None
                and channel.rpm is not None
                and abs(updated[channel.identifier].rpm - channel.rpm)
                >= max(100, int(channel.rpm * 0.05))
            )
        ]
        self.last_feedback = (
            "PWM e modalità confermati dal driver. Variazione RPM osservata, "
            "non attribuibile con certezza al preset."
            if rpm_changes
            else "PWM e modalità confermati dal driver, ma RPM sostanzialmente "
            "invariati: il firmware potrebbe mantenere il controllo."
        )

    def restore_original(self) -> None:
        if self.current_preset == "automatic":
            return
        self.refresh()
        payload = []
        for channel in self.controllable_channels:
            baseline = self._baseline.get(channel.identifier)
            if baseline is None:
                continue
            payload.append(
                {
                    "pwm": str(channel.pwm_path),
                    "enable": str(channel.enable_path),
                    "value": baseline.pwm_value,
                    "enable_mode": baseline.enable_mode,
                }
            )
        if not payload:
            return
        self._run_helper("restore", payload)
        self.current_preset = "automatic"
        self.last_feedback = "Stato precedente ripristinato."
        self.refresh()

    def _run_helper(self, operation: str, payload: Iterable[dict[str, object]]) -> None:
        pkexec = self._pkexec()
        if pkexec is None:
            raise FanControlError("pkexec non è installato")
        if not self.helper_trust_checker(self.helper_path):
            raise FanControlError(
                "helper ventole non installato o non sicuro; esegui "
                "scripts/install-fan-helper.sh"
            )
        command = [
            pkexec,
            str(self.helper_path),
            operation,
            json.dumps(list(payload), separators=(",", ":")),
        ]
        try:
            result = self.runner(
                command,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise FanControlError(f"impossibile avviare l'helper: {exc}") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            if not detail:
                detail = "autorizzazione amministrativa negata o annullata"
            raise FanControlError(detail)
