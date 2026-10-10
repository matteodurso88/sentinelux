#!/usr/bin/env python3
"""Read-only report of fan RPM/PWM controls exposed by Linux hwmon."""

from __future__ import annotations

import shutil
import stat
from pathlib import Path

from sentinelux.fans import discover_fans


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return "non leggibile"


def describe(path: Path | None) -> str:
    if path is None:
        return "assente"
    try:
        bits = stat.S_IMODE(path.stat().st_mode)
        modes = stat.filemode(path.stat().st_mode)
    except OSError:
        return f"{path}: non verificabile"
    return f"{path} · {modes} ({bits:04o}) · valore={read(path)}"


def main() -> None:
    dmi_name = read(Path("/sys/class/dmi/id/product_name"))
    print(f"Modello sistema: {dmi_name}")
    cli = shutil.which("smbios-thermal-ctl")
    print(f"Interfaccia Dell thermal profile: {cli or 'non installata'}")
    profile = Path("/sys/firmware/acpi/platform_profile")
    choices = Path("/sys/firmware/acpi/platform_profile_choices")
    print(f"Profilo termico kernel: {read(profile) if profile.is_file() else 'assente'}")
    print(f"Profili disponibili: {read(choices) if choices.is_file() else 'assenti'}")
    channels = discover_fans()
    print(f"Canali hwmon rilevati: {len(channels)}")
    for channel in channels:
        print()
        print(f"{channel.identifier} · driver={channel.chip} · {channel.label}")
        print(f"RPM: {channel.rpm if channel.rpm is not None else 'n.d.'}")
        print(f"Controllabile secondo il contratto generico: {channel.controllable}")
        print(f"fan_input: {describe(channel.fan_input_path)}")
        print(f"pwm:       {describe(channel.pwm_path)}")
        print(f"pwm_enable:{describe(channel.enable_path)}")
    print()
    print("Diagnostica in sola lettura: nessun valore e' stato scritto a sysfs.")


if __name__ == "__main__":
    main()
