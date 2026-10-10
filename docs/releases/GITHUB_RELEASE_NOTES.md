# Sentinelux v0.1.0-alpha.1

First public **alpha prerelease** of Sentinelux, an open-source Linux desktop hardware monitor.

### What's included

- Compact GTK 3/AppIndicator tray for CPU usage, Linux RAM pressure and swap.
- CPU hottest temperature and optional package-level temperature.
- Scrollable, updating details for all detected CPU thermal sensors; package is **not** counted as a core. Contiguous `Core 1…N` labels retain underlying hwmon IDs in tooltips.
- Configurable thermal warning, critical, reminder and recovery notifications.
- Optional preventive suspend/hibernate request via systemd-logind (disabled by default).
- **Read-only** fan RPM, PWM and mode display when provided by Linux.
- Per-user installation, autostart, and a one-shot JSON metrics command.

### Source installation (Debian-family desktops)

Requires Python 3.10+, GTK 3, PyGObject, psutil, libnotify and an AppIndicator-compatible tray.

```bash
git clone https://github.com/matteodurso88/sentinelux.git
cd sentinelux
git checkout v0.1.0-alpha.1
./scripts/install-deps-debian.sh
./scripts/install-user.sh
~/.local/bin/sentinelux --version
~/.local/bin/sentinelux --debug
```

**Known limits:** alpha release, no signed binary, `.deb` or APT repository; no full dashboard or metric history; sensor and tray support vary by hardware/desktop. The user interface is in Italian; documentation is bilingual.

**Fan safety:** manual fan speed / PWM presets and the privileged fan helper are **not included**. This release only reads telemetry; the BIOS and firmware continue to govern cooling.

**Validation provenance:** Dell Latitude 5440 installation and installed `0.1.0a1` version were confirmed by the owner. The full local unittest/compileall/CLI gate log has **not** been supplied; this prerelease must not be represented as fully tested or stable.

Documentation: [Italiano](https://github.com/matteodurso88/sentinelux/blob/main/README.it.md) · [English](https://github.com/matteodurso88/sentinelux/blob/main/README.en.md).
