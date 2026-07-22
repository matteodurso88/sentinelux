#!/usr/bin/python3
"""Minimal privileged writer for validated Linux hwmon PWM attributes."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


HWMON_PATH_RE = re.compile(
    r"^/sys/class/hwmon/hwmon\d+/(pwm\d+|pwm\d+_enable)$"
)


class HelperError(RuntimeError):
    pass


def _validated_path(raw: object, *, suffix: str) -> Path:
    if not isinstance(raw, str) or not HWMON_PATH_RE.fullmatch(raw):
        raise HelperError("percorso hwmon non valido")
    path = Path(raw)
    if not path.name.endswith(suffix):
        raise HelperError("attributo hwmon inatteso")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise HelperError(f"attributo hwmon non disponibile: {path}") from exc
    if not resolved.is_relative_to(Path("/sys/devices")):
        raise HelperError("attributo esterno a /sys/devices")
    if not path.is_file():
        raise HelperError(f"attributo hwmon non scrivibile: {path}")
    return path


def _integer(entry: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = entry.get(key)
    if not isinstance(value, int) or not minimum <= value <= maximum:
        raise HelperError(f"valore {key} non valido")
    return value


def _write(path: Path, value: int) -> None:
    try:
        path.write_text(f"{value}\n", encoding="ascii")
    except OSError as exc:
        raise HelperError(f"scrittura fallita su {path}: {exc}") from exc


def apply_operation(operation: str, payload: object) -> None:
    if operation not in {"manual", "automatic", "restore"}:
        raise HelperError("operazione non supportata")
    if not isinstance(payload, list) or not payload:
        raise HelperError("payload vuoto o non valido")

    validated: list[tuple[Path, Path, dict[str, Any]]] = []
    for raw_entry in payload:
        if not isinstance(raw_entry, dict):
            raise HelperError("canale non valido")
        pwm = _validated_path(raw_entry.get("pwm"), suffix="")
        if not re.fullmatch(r"pwm\d+", pwm.name):
            raise HelperError("attributo PWM non valido")
        enable = _validated_path(raw_entry.get("enable"), suffix="_enable")
        validated.append((pwm, enable, raw_entry))

    for pwm, enable, entry in validated:
        if operation == "manual":
            value = _integer(entry, "value", 0, 255)
            _write(enable, 1)
            _write(pwm, value)
        elif operation == "automatic":
            value = _integer(entry, "value", 0, 255)
            mode = _integer(entry, "enable_mode", 2, 255)
            _write(pwm, value)
            _write(enable, mode)
        else:
            value = _integer(entry, "value", 0, 255)
            mode = _integer(entry, "enable_mode", 0, 255)
            _write(pwm, value)
            _write(enable, mode)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.geteuid() != 0:
        print("sentinelux fan helper: sono richiesti privilegi amministrativi", file=sys.stderr)
        return 2
    if len(args) != 2:
        print("sentinelux fan helper: argomenti non validi", file=sys.stderr)
        return 2
    operation, raw_payload = args
    try:
        payload = json.loads(raw_payload)
        apply_operation(operation, payload)
    except (HelperError, json.JSONDecodeError) as exc:
        print(f"sentinelux fan helper: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
