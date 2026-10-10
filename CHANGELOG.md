# Changelog

All notable changes to Sentinelux will be documented in this file.

## [Next] - Unreleased

### Changed

- The main tray now shows CPU maximum temperature and an optional package-level reading.
- Added a bounded, scrollable and live-updated GTK details window for all CPU temperature sensors.
- Sensor collection, thermal alert thresholds and preventive protection continue using complete temperature readings.

## [0.0.5] - Unreleased

### Documentation

- Added Italian and English GitHub documentation with a bilingual landing README.
- Added the public Sentinelux product dossier and matt88.it handoff under `docs/public/`.

### Changed

- Made the tray RAM percentage and used/total values derive from the same `MemAvailable` accounting model.
- Added currently available memory to the flat tray row.
- Kept the raw psutil `used` value in metrics while exposing explicit available and unavailable byte counts.

## [0.0.4] - Unreleased

### Added

- Read-only fan RPM, PWM percentage, and control-mode discovery through Linux hwmon.
- Flat tray rows for every fan exposed by the kernel.
- A Ventole preferences page with Automatico, Silenzioso, Bilanciato, Prestazioni, and Massimo presets.
- Session-scoped privileged PWM writes through a narrowly validated, root-owned `pkexec` helper.
- Tachometer feedback checks after manual preset changes and automatic restoration of the original fan state on exit.

### Safety

- Manual control is offered only when RPM, PWM, and readable control mode are all exposed.
- The lowest manual preset is 55%; Sentinelux never offers a fan-off preset.
- No fan preset is applied automatically at login or persisted in the JSON configuration.

## [0.0.3] - Unreleased

### Added

- Preventive thermal protection with configurable hibernation or suspension.
- Configurable action temperature, persistence time, and cancellation hysteresis.
- Read-only discovery and display of Linux thermal-zone critical trip points.
- systemd-logind capability reporting before enabling a sleep action.
- Sustained-temperature controller that cancels the pending action after recovery.

## [0.0.2] - Unreleased

### Changed

- Replaced the sectioned tray layout with a compact single-level menu.
- Added icon-prefixed rows with CPU, RAM, swap, package, and every detected core value visible immediately.
- Moved thermal state and hottest temperature into the one-line Sentinelux header.
- Kept preferences and per-alert controls without a sensor submenu.
- Reworked metric rows as standard AppIndicator-compatible menu labels.
- Added an Avvio preferences page to enable or disable XDG autostart.

## [0.0.1] - Unreleased

### Added

- GTK 3 tray application using Ayatana AppIndicator or legacy AppIndicator fallback.
- Styled and sectioned tray menu for CPU, RAM, swap, and thermal state.
- CPU package and per-core temperature monitoring when exposed by the system.
- Hottest-sensor alert policy with maximum, average, and detailed readings.
- Warning, critical, reminder, and recovery notifications.
- Independent persistent controls for every notification type.
- GTK preferences page for thresholds, timing, and alert management.
- CPU temperature discovery through psutil and Linux sysfs fallbacks.
- Per-user installation, launcher, desktop entry, and optional autostart scripts.
- JSON configuration and command-line overrides.
- Initial unit tests and verification scripts.
