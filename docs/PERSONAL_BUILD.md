# Personal build status — 0.0.5

This build is intentionally focused so it can be used immediately on the maintainer's Linux workstation while the packaging and broader hardware roadmap remain open.

## Included

- compact single-level tray menu;
- total CPU utilisation;
- coherent RAM pressure, unavailable/total and available memory;
- swap utilisation;
- CPU package and per-core temperature discovery;
- hottest-sensor thermal policy;
- warning, critical, reminder and recovery notifications;
- GTK preferences for monitoring, alerts, preventive protection, fans and startup;
- per-user installation and optional XDG autostart;
- read-only kernel critical trip-point display;
- optional preventive hibernation or suspension when logind authorizes it;
- read-only fan telemetry and temporary `pkexec`-authorized PWM presets when safely exposed by hwmon;
- one-shot JSON metrics output.

## Temperature model

Sentinelux selects the most plausible CPU sensor group and keeps all useful readings from that group. On Intel systems this can include `Package id 0` and one entry per core. Other hardware may expose package-level readings such as `Tctl` or `Tdie`, or no suitable CPU temperature at all.

The tray shows every selected reading. Alert and preventive-protection decisions use the hottest selected value.

## Not included yet

- historical graphs and metric storage;
- battery and power telemetry;
- storage and SMART monitoring;
- network monitoring;
- process listing or management;
- advanced or persistent fan curves;
- `.deb` package and APT repository;
- automatic software updates;
- formal Wayland and multi-desktop compatibility matrix;
- runtime English localization;
- matt88.it product-page implementation.

## Safe notification test

To trigger notifications without heating the machine, temporarily start Sentinelux with deliberately low thresholds:

```bash
./scripts/run-dev.sh \
  --warning-temp 30 \
  --critical-temp 40 \
  --debug
```

Exit the application from its tray menu and restart it normally afterward.

## Fan-control safety and Dell diagnostics

Fan control is not guaranteed by a successful `pkexec` helper exit.
The manager now checks PWM and mode values read back from `hwmon` and warns
if the tachometer fails to show meaningful change. On Dell SMM systems, the
BIOS may override requested fan levels. When the Linux kernel exposes `/sys/firmware/acpi/platform_profile`,
Sentinelux now uses its advertised native thermal profiles instead of generic
PWM percentages. The Dell Latitude 5440 reported `cool quiet balanced
performance` and current `balanced`. No extra SMBIOS package is necessary.
The installed root-owned fan helper must be refreshed with
`./scripts/install-fan-helper.sh` before testing this branch.

Kernel thermal profiles are policies, not an RPM guarantee. PWM on
`dell_smm` is disabled as a manual control backend, but read-only RPM
telemetry remains available.

Read-only capability check (no `sudo`, no sysfs writes):

```bash
PYTHONPATH=src python3 scripts/diagnose-fans.py
```

The helper's native profile operation writes only the allowlisted values
`quiet`, `balanced`, `performance`, or `cool` to the fixed kernel
`platform_profile` endpoint. It rejects unsupported or arbitrary strings.
A local gate must verify the installed helper, readback and actual device
behavior before integration.

Apply/test PWM presets on actual hardware only with verified reversible
control and observe RPM, CPU temperature, and driver mode. Never bypass
firmware protections or force unsupported SMM codes.

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
