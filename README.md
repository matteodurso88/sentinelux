# Sentinelux

Sentinelux is a tray-first Linux hardware monitor focused on lightweight, local system health visibility and thermal alerts.

The first personal build provides:

- total CPU usage;
- RAM and swap usage;
- CPU package and per-core temperature detection when exposed by the hardware;
- thermal policy based on the hottest detected CPU sensor;
- warning, critical, reminder, and recovery desktop notifications;
- independent enable/disable controls for each alert type;
- a compact single-level GTK tray menu with icon-prefixed values and every detected CPU sensor visible;
- a GTK preferences page for thresholds, refresh interval, notifications, and automatic startup;
- JSON configuration under `~/.config/sentinelux/config.json`;
- no root requirement, telemetry, or network activity.

## Supported systems

The bootstrap build targets Debian-family desktop distributions with GTK 3 and an AppIndicator-compatible tray implementation.

## Quick start

```bash
./scripts/install-deps-debian.sh
./scripts/run-dev.sh --debug
```

Open **Preferenze…** from the tray menu to configure:

- refresh interval;
- warning and critical thresholds;
- recovery hysteresis;
- reminder interval;
- notification master switch;
- warning, critical, reminder, and recovery alert types;
- automatic startup at desktop login.

Install for the current user:

```bash
./scripts/install-user.sh
~/.local/bin/sentinelux --debug
```

Enable autostart from **Preferenze… → Avvio**, or from the terminal:

```bash
./scripts/enable-autostart.sh
```

Print one metrics snapshot without starting the GUI:

```bash
./scripts/run-dev.sh --once
```

The JSON snapshot includes the hottest CPU temperature, the average of the selected sensor group, and the complete package/core reading list.

## Default thermal policy

- warning: 85 °C;
- critical: 95 °C;
- recovery hysteresis: 5 °C;
- reminder interval while hot: 5 minutes.

Sentinelux applies these thresholds to the hottest selected package/core sensor. Values can be changed from the GTK preferences page, directly in the JSON configuration, or temporarily overridden from the command line.

## Project status

This is an early personal-use bootstrap. Storage, battery, power, network, graphs, fan controls, Debian packaging, and the matt88.it product-page integration are deferred.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
