# Changelog

All notable changes to Sentinelux will be documented in this file.

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
