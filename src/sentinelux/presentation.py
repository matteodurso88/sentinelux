"""Pure presentation helpers for the Sentinelux tray UI."""

from __future__ import annotations

import re
from typing import Sequence

from .alerts import ThermalState
from .metrics import TemperatureReading, human_bytes


_STATE_PRESENTATION = {
    ThermalState.NORMAL: ("Normale", "#2e7d32"),
    ThermalState.WARNING: ("Attenzione", "#f9a825"),
    ThermalState.CRITICAL: ("Critico", "#c62828"),
}


def format_percentage(value: float) -> str:
    """Format a percentage with one decimal place."""

    return f"{value:.1f}%"


def format_memory_summary(
    percent: float,
    unavailable_bytes: int,
    total_bytes: int,
    available_bytes: int,
) -> str:
    """Format coherent Linux memory pressure and availability values."""

    return (
        f"{format_percentage(percent)} · "
        f"{human_bytes(unavailable_bytes)} / {human_bytes(total_bytes)} · "
        f"disp. {human_bytes(available_bytes)}"
    )


def format_temperature(value_c: float | None) -> str:
    """Format a Celsius reading for compact tray display."""

    return "non disponibile" if value_c is None else f"{value_c:.1f} °C"


def sensor_display_name(label: str) -> str:
    """Return a short, consistent name for a CPU temperature sensor."""

    clean = " ".join((label or "").split()) or "Temperatura CPU"

    package_match = re.fullmatch(
        r"package(?:\s+id)?\s*(\d+)?",
        clean,
        flags=re.IGNORECASE,
    )
    if package_match:
        number = package_match.group(1)
        return f"CPU Package {number}" if number is not None else "CPU Package"

    core_match = re.fullmatch(r"core\s*(\d+)", clean, flags=re.IGNORECASE)
    if core_match:
        return f"Core {core_match.group(1)}"

    cpu_match = re.fullmatch(r"cpu\s*(\d+)", clean, flags=re.IGNORECASE)
    if cpu_match:
        return f"CPU {cpu_match.group(1)}"

    aliases = {
        "tctl": "CPU Tctl",
        "tdie": "CPU Tdie",
        "physical id 0": "CPU Package 0",
    }
    return aliases.get(clean.lower(), clean)


def thermal_state_presentation(state: ThermalState) -> tuple[str, str]:
    """Return the localized label and foreground colour for a thermal state."""

    return _STATE_PRESENTATION[state]


def primary_cpu_sensor(
    readings: Sequence[TemperatureReading],
) -> TemperatureReading | None:
    """Choose the best package-level sensor to show in the compact tray.

    Core-only systems intentionally have no second summary row. The full
    sensor collection remains available for the detail window and thermal policy.
    """
    def priority(reading: TemperatureReading) -> int:
        label = " ".join(reading.label.lower().split())
        if re.fullmatch(r"(?:cpu\s+)?package(?:\s+id)?\s*\d*", label):
            return 0
        if re.fullmatch(r"physical\s+id\s*\d+", label):
            return 0
        if label == "tctl":
            return 1
        if label == "tdie":
            return 2
        return 3

    candidates = (reading for reading in readings if priority(reading) < 3)
    return min(candidates, key=priority, default=None)


def _hardware_core_id(label: str) -> int | None:
    """Extract the Linux hwmon core ID, which need not be contiguous."""
    match = re.fullmatch(r"core\s*(\d+)", " ".join((label or "").split()), re.IGNORECASE)
    return int(match.group(1)) if match is not None else None


def count_core_sensors(readings: Sequence[TemperatureReading]) -> int:
    """Count only per-core temperature sensors, never package-level sensors."""
    return sum(_hardware_core_id(reading.label) is not None for reading in readings)


def sensor_detail_names(readings: Sequence[TemperatureReading]) -> tuple[str, ...]:
    """Number core rows consecutively without changing the original hwmon data.

    Ordinals follow hardware core-ID order; kernel IDs remain accessible via
    the detail-row tooltip for diagnostics.
    """
    core_positions = sorted(
        (
            (index, core_id)
            for index, reading in enumerate(readings)
            if (core_id := _hardware_core_id(reading.label)) is not None
        ),
        key=lambda pair: (pair[1], pair[0]),
    )
    numbering = {
        index: ordinal for ordinal, (index, _core_id) in enumerate(core_positions, 1)
    }
    return tuple(
        f"Core {numbering[index]}"
        if index in numbering
        else sensor_display_name(reading.label)
        for index, reading in enumerate(readings)
    )


def sensor_count_summary(readings: Sequence[TemperatureReading]) -> str:
    """Distinguish core sensor count from total CPU temperature readings."""
    cores = count_core_sensors(readings)
    if cores:
        return f"{cores} core monitorati · {len(readings)} sensori CPU"
    return f"Sensori CPU · {len(readings)}"
