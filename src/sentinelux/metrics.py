"""System metrics and multicore CPU-temperature discovery."""

from __future__ import annotations

import glob
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


CPU_CHIP_HINTS = (
    "coretemp",
    "k10temp",
    "zenpower",
    "cpu_thermal",
    "cpu-thermal",
    "x86_pkg_temp",
    "soc_thermal",
    "soc-thermal",
)
CPU_LABEL_HINTS = (
    "package id",
    "physical id",
    "tctl",
    "tdie",
    "cpu",
    "core",
    "soc",
)
EXCLUDED_HINTS = (
    "nvme",
    "amdgpu",
    "radeon",
    "gpu",
    "iwlwifi",
    "wifi",
    "wireless",
    "pch",
)


@dataclass(frozen=True, slots=True)
class TemperatureReading:
    value_c: float
    source: str
    label: str


@dataclass(frozen=True, slots=True)
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    memory_used_bytes: int
    memory_total_bytes: int
    swap_percent: float
    swap_used_bytes: int
    swap_total_bytes: int
    cpu_temperature_c: float | None
    cpu_temperature_average_c: float | None
    temperature_source: str | None
    temperature_label: str | None
    temperature_readings: tuple[TemperatureReading, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def human_bytes(value: int) -> str:
    """Format a byte count using binary units."""

    size = float(max(value, 0))
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0
    raise AssertionError("unreachable")


def _normalise(text: str | None) -> str:
    return (text or "").strip().lower().replace("-", "_")


def _is_valid_temperature(value: float) -> bool:
    return math.isfinite(value) and -20.0 <= value <= 150.0


def _chip_score(chip: str) -> int:
    chip_n = _normalise(chip)
    if any(hint in chip_n for hint in EXCLUDED_HINTS):
        return -100
    if any(hint.replace("-", "_") in chip_n for hint in CPU_CHIP_HINTS):
        return 100
    if chip_n in {"acpitz", "thermal_zone"}:
        return 5
    return 0


def _candidate_score(chip: str, label: str) -> int:
    chip_n = _normalise(chip)
    label_n = _normalise(label)
    combined = f"{chip_n} {label_n}"

    if any(hint in combined for hint in EXCLUDED_HINTS):
        return -100

    score = _chip_score(chip)
    if any(hint in label_n for hint in CPU_LABEL_HINTS):
        score += 40
    if "package" in label_n or "tctl" in label_n or "tdie" in label_n:
        score += 20
    return score


def _reading_sort_key(reading: TemperatureReading) -> tuple[int, int, str]:
    label = _normalise(reading.label)
    if any(hint in label for hint in ("package", "tctl", "tdie", "physical")):
        return (0, 0, label)
    match = re.search(r"(?:core|cpu)\s*(\d+)", label)
    if match:
        return (1, int(match.group(1)), label)
    return (2, 0, label)


def choose_cpu_temperatures(
    candidates: Iterable[TemperatureReading],
) -> tuple[TemperatureReading, ...]:
    """Return all useful readings from the most plausible CPU sensor group.

    A single hwmon chip commonly exposes one package sensor plus one reading per
    physical core. Sentinelux keeps that complete group and uses its hottest
    reading for the thermal policy.
    """

    groups: dict[str, list[TemperatureReading]] = {}
    source_names: dict[str, str] = {}

    for candidate in candidates:
        if not _is_valid_temperature(candidate.value_c):
            continue
        if _candidate_score(candidate.source, candidate.label) <= 0:
            continue
        source_key = _normalise(candidate.source)
        groups.setdefault(source_key, []).append(candidate)
        source_names[source_key] = candidate.source

    if not groups:
        return ()

    def group_rank(item: tuple[str, list[TemperatureReading]]) -> tuple[int, int, int, float]:
        source_key, readings = item
        meaningful = sum(
            1
            for reading in readings
            if any(hint in _normalise(reading.label) for hint in CPU_LABEL_HINTS)
        )
        return (
            _chip_score(source_names[source_key]),
            meaningful,
            len(readings),
            max(reading.value_c for reading in readings),
        )

    _best_source, selected = max(groups.items(), key=group_rank)

    deduplicated: dict[str, TemperatureReading] = {}
    for reading in selected:
        key = _normalise(reading.label) or "sensor"
        previous = deduplicated.get(key)
        if previous is None or reading.value_c > previous.value_c:
            deduplicated[key] = reading

    return tuple(sorted(deduplicated.values(), key=_reading_sort_key))


def choose_cpu_temperature(
    candidates: Iterable[TemperatureReading],
) -> TemperatureReading | None:
    """Select the hottest reading from the best CPU sensor group."""

    readings = choose_cpu_temperatures(candidates)
    return max(readings, key=lambda reading: reading.value_c) if readings else None


def _psutil_candidates(
    sensors: Mapping[str, Sequence[Any]],
) -> list[TemperatureReading]:
    readings: list[TemperatureReading] = []
    for chip, entries in sensors.items():
        for entry in entries:
            current = getattr(entry, "current", None)
            if current is None:
                continue
            try:
                value = float(current)
            except (TypeError, ValueError):
                continue
            label = str(getattr(entry, "label", "") or chip)
            readings.append(TemperatureReading(value, chip, label))
    return readings


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
    return value if _is_valid_temperature(value) else None


def _sysfs_hwmon_candidates() -> list[TemperatureReading]:
    readings: list[TemperatureReading] = []
    for raw_dir in glob.glob("/sys/class/hwmon/hwmon*"):
        directory = Path(raw_dir)
        chip = _read_text(directory / "name") or directory.name
        for input_path in directory.glob("temp*_input"):
            value = _read_millidegrees(input_path)
            if value is None:
                continue
            stem = input_path.name.removesuffix("_input")
            label = _read_text(directory / f"{stem}_label") or stem
            readings.append(TemperatureReading(value, chip, label))
    return readings


def _sysfs_thermal_candidates() -> list[TemperatureReading]:
    readings: list[TemperatureReading] = []
    for raw_dir in glob.glob("/sys/class/thermal/thermal_zone*"):
        directory = Path(raw_dir)
        zone_type = _read_text(directory / "type") or directory.name
        value = _read_millidegrees(directory / "temp")
        if value is None:
            continue
        readings.append(TemperatureReading(value, zone_type, zone_type))
    return readings


def read_cpu_temperatures(
    psutil_module: Any | None = None,
) -> tuple[TemperatureReading, ...]:
    """Read all CPU/package/core temperatures from the best available source."""

    if psutil_module is None:
        try:
            import psutil as psutil_module  # type: ignore[no-redef]
        except ImportError:
            psutil_module = None

    if psutil_module is not None:
        sensor_fn = getattr(psutil_module, "sensors_temperatures", None)
        if callable(sensor_fn):
            try:
                sensors = sensor_fn(fahrenheit=False)
            except (OSError, RuntimeError):
                sensors = {}
            selected = choose_cpu_temperatures(_psutil_candidates(sensors or {}))
            if selected:
                return selected

    selected = choose_cpu_temperatures(_sysfs_hwmon_candidates())
    if selected:
        return selected

    return choose_cpu_temperatures(_sysfs_thermal_candidates())


def read_cpu_temperature(psutil_module: Any | None = None) -> TemperatureReading | None:
    """Compatibility helper returning the hottest CPU reading."""

    readings = read_cpu_temperatures(psutil_module)
    return max(readings, key=lambda reading: reading.value_c) if readings else None


def collect_metrics(psutil_module: Any | None = None) -> SystemMetrics:
    """Collect one system-health snapshot."""

    if psutil_module is None:
        try:
            import psutil as psutil_module  # type: ignore[no-redef]
        except ImportError as exc:
            raise RuntimeError(
                "psutil is required; run scripts/install-deps-debian.sh"
            ) from exc

    memory = psutil_module.virtual_memory()
    swap = psutil_module.swap_memory()
    temperature_readings = read_cpu_temperatures(psutil_module)
    hottest = (
        max(temperature_readings, key=lambda reading: reading.value_c)
        if temperature_readings
        else None
    )
    average = (
        sum(reading.value_c for reading in temperature_readings)
        / len(temperature_readings)
        if temperature_readings
        else None
    )

    return SystemMetrics(
        cpu_percent=float(psutil_module.cpu_percent(interval=None)),
        memory_percent=float(memory.percent),
        memory_used_bytes=int(memory.used),
        memory_total_bytes=int(memory.total),
        swap_percent=float(swap.percent),
        swap_used_bytes=int(swap.used),
        swap_total_bytes=int(swap.total),
        cpu_temperature_c=(hottest.value_c if hottest else None),
        cpu_temperature_average_c=average,
        temperature_source=(hottest.source if hottest else None),
        temperature_label=(hottest.label if hottest else None),
        temperature_readings=temperature_readings,
    )
