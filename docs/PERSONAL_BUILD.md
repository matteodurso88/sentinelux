# Personal build 0.0.1

This bootstrap is intentionally narrow so it can be used immediately on the maintainer's Linux workstation.

## Included

- styled tray icon and sectioned menu;
- CPU utilisation;
- RAM and swap utilisation;
- CPU package and per-core temperature discovery;
- hottest-sensor thermal policy;
- package and per-core temperatures visible directly in the tray menu;
- GTK preferences page;
- configurable warning, critical, reminder, and recovery alert types;
- user-local install and optional autostart controlled from the preferences window;
- configurable thresholds without root privileges.

## Temperature model

Sentinelux selects the most plausible CPU sensor group and keeps all useful readings from that group. On Intel systems this commonly includes `Package id 0` and one entry per physical core. On other hardware the kernel may expose only package-level readings such as `Tctl` or `Tdie`.

The tray displays maximum and average values. Alert transitions always use the hottest selected reading.

## Not included yet

- historical graphs;
- battery and power telemetry;
- storage and SMART monitoring;
- network monitoring;
- fan-speed control;
- `.deb` package and APT repository;
- Wayland/desktop-environment-specific integration beyond AppIndicator;
- matt88.it product-page integration.

## Safe notification test

To trigger notifications without heating the machine, temporarily start Sentinelux with deliberately low thresholds:

```bash
./scripts/run-dev.sh \
  --warning-temp 30 \
  --critical-temp 40 \
  --debug
```

Exit the application from its tray menu and restart it normally afterward.

## Temperature diagnostics

When no CPU temperature is detected, collect these outputs:

```bash
sensors
python3 - <<'PY'
import pprint
import psutil
pprint.pp(psutil.sensors_temperatures())
PY
find /sys/class/thermal -maxdepth 2 -type f \
  \( -name type -o -name temp \) -print
```
