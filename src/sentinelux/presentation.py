"""Pure presentation helpers for the Sentinelux tray UI."""

from __future__ import annotations

import re

from .alerts import ThermalState
from .metrics import human_bytes


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
