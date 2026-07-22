# Sentinelux

[Documentazione italiana](README.it.md) · [Bilingual README](README.md)

Sentinelux is an open-source hardware monitor for Linux desktops. It keeps essential information in the system tray: CPU load, coherent RAM pressure, swap usage, CPU temperatures and fan telemetry when the kernel exposes it. The current goal is immediate visibility and configurable thermal alerts without turning the application into an intrusive dashboard.

> **Status:** version `0.0.5`, pre-alpha, not yet published as a release or `.deb` package.

## Available features

- tray icon with the hottest temperature or CPU-load label;
- flat menu showing CPU, RAM, swap, package/core sensors and fans;
- RAM accounting based on available memory, using a coherent pattern:
  `▣ RAM · 61.4% · 2.3 GiB / 3.8 GiB · disp. 1.4 GiB`;
- selection of the most plausible CPU sensor group, with the hottest reading driving the thermal policy;
- warning, critical, reminder and recovery notifications;
- configurable thresholds, hysteresis, intervals and alert types;
- persistent preferences in `~/.config/sentinelux/config.json`;
- XDG autostart controlled from the preferences window;
- optional preventive hibernation or suspension;
- read-only display of the lowest kernel-exported `critical` thermal trip point;
- fan discovery through `hwmon`, with PWM control only when the channel can be verified;
- JSON snapshot export through `--once`;
- per-user installation and removal scripts.

## Confirmed requirements

Sentinelux currently targets Debian-family Linux desktops and requires:

- Python 3.10 or newer;
- GTK 3 and PyGObject;
- `psutil`;
- Ayatana AppIndicator or the legacy AppIndicator fallback;
- libnotify;
- `systemd-logind`, `busctl` and `systemctl` for preventive sleep actions;
- `pkexec` only for optional PWM presets;
- a desktop session with an AppIndicator-compatible tray.

The available local validation was performed on an Xfce/X11 environment. The exact distribution version, Wayland and other CPU architectures have not been formally verified yet.

## Development mode

```bash
./scripts/install-deps-debian.sh
./scripts/run-dev.sh --debug
```

The configuration file is created on first run. To print one snapshot without starting the GUI:

```bash
./scripts/run-dev.sh --once
```

Useful options:

```text
--version
--once
--debug
--no-notifications
--warning-temp CELSIUS
--critical-temp CELSIUS
--interval SECONDS
```

## Per-user installation

```bash
./scripts/install-user.sh
~/.local/bin/sentinelux --debug
```

The installer copies Sentinelux to:

```text
~/.local/share/sentinelux
~/.local/bin/sentinelux
~/.local/share/applications/io.matt88.Sentinelux.desktop
```

Autostart can be managed from **Preferences → Startup** or from the terminal:

```bash
./scripts/enable-autostart.sh
./scripts/disable-autostart.sh
```

The current runtime interface is Italian; the English labels in this document describe the corresponding controls.

## Configuration

The **Preferences** window contains:

- **Monitoring** — interval, warning threshold, critical threshold, hysteresis and reminders;
- **Alerts** — master switch and individual notification types;
- **Protection** — preventive action, threshold, persistence, hysteresis and read-only kernel trip point;
- **Fans** — `hwmon` telemetry and PWM presets when supported;
- **Startup** — XDG autostart.

Configuration is written atomically to:

```text
~/.config/sentinelux/config.json
```

## Preventive thermal protection

Protection is disabled by default. When enabled, Sentinelux requires the hottest temperature to remain above the configured threshold for a minimum duration. If it drops below the threshold minus the recovery hysteresis, the pending action is cancelled.

Available actions:

- hibernation;
- suspension.

Sentinelux queries `systemd-logind` to determine whether the action is available and authorized. It does not change kernel, BIOS, firmware or hardware limits. The `critical` threshold displayed in the GUI is read from `/sys/class/thermal` and may not represent every protection implemented by the computer.

## Fans and PWM presets

Sentinelux reads channels exported through `/sys/class/hwmon`. The page remains read-only unless the system exposes all of the following:

- `fanN_input` tachometer feedback;
- a `pwmN` value;
- a readable `pwmN_enable` mode.

On compatible hardware, install the privileged helper once:

```bash
./scripts/install-fan-helper.sh
```

Session presets:

- Automatic;
- Quiet · 55%;
- Balanced · 70%;
- Performance · 85%;
- Maximum · 100%.

There is no zero-speed preset. Sentinelux checks RPM feedback after a manual change and attempts to restore the initial state during a normal exit. Presets are not persisted and are never applied automatically at login. Remove the helper with:

```bash
./scripts/uninstall-fan-helper.sh
```

## Data, network and privileges

During normal monitoring, Sentinelux reads local metrics through `psutil`, `/sys/class/hwmon` and `/sys/class/thermal`. The runtime contains no telemetry, cloud synchronization or network calls.

Administrative privileges are not required for the tray, metrics, configuration or per-user installation. They are required only to:

- install system dependencies;
- install or remove the fan helper;
- apply PWM presets through `pkexec`, when supported;
- execute hibernation or suspension according to system policy.

## Tests

Run locally with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Verified on 22 July 2026: **42 unit tests passed**. No CI/CD workflow is currently included in the repository.

## Current limitations

Not implemented yet:

- full monitoring dashboard and historical details;
- battery and power telemetry;
- storage and SMART data;
- network monitoring;
- process listing and management;
- graphs;
- English runtime localization;
- `.deb` package, APT repository and automatic updates;
- publishable branded assets and sanitized screenshots.

## Updating and uninstalling

There is no integrated updater yet. After updating the source tree, rerun:

```bash
./scripts/install-user.sh
```

To uninstall:

```bash
./scripts/uninstall-user.sh
```

The script intentionally retains `~/.config/sentinelux`. The fan helper, when installed, must be removed separately.

## Contributing

The repository is public and the project-declared issue tracker is:

`https://github.com/matteodurso88/sentinelux/issues`

A formal contribution guide is not available yet. Opening a descriptive issue before a large change is recommended.

## License

Sentinelux is licensed under **GPL-3.0-or-later**. See [LICENSE](LICENSE).
