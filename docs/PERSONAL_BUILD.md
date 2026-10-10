# Release candidate — v0.1.0-alpha.1 (not yet published)

This build is intentionally focused so it can be used immediately on the maintainer's Linux workstation while the packaging and broader hardware roadmap remain open.

## Included

- compact AppIndicator tray with hottest and available package-level CPU temperatures;
- scrollable GTK details window with all detected CPU temperature sensors;
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
- read-only fan telemetry via Linux `hwmon`, without PWM writes, presets or a privileged helper;
- one-shot JSON metrics output.

## Temperature model

Sentinelux selects the most plausible CPU sensor group and keeps all useful readings from that group. On Intel systems this can include `Package id 0` and one entry per core. Other hardware may expose package-level readings such as `Tctl` or `Tdie`, or no suitable CPU temperature at all.

The tray shows the hottest CPU reading and, when available, a package-level reading (Package, Tctl or Tdie). The “Dettaglio sensori termici” item opens a bounded, scrollable GTK window containing every selected sensor; readings update during normal refreshes. Its core count excludes the additional package-level sensor: e.g. 14 core sensors and one Package reading are presented as 14 monitored cores / 15 total CPU sensors. The displayed core numbers are contiguous ordinals (1–14 in that example), while their original kernel/hwmon labels (which can be spaced by four or otherwise non-contiguous) remain in each row's tooltip. This is a count of detected per-core temperature sensors, not an independent hardware-topology inventory. Systems exposing only core readings keep the tray to one temperature row. Alert and preventive-protection decisions continue to use the hottest selected value, independently of what is visible in the tray.

## Not included yet

- historical graphs and metric storage;
- battery and power telemetry;
- storage and SMART monitoring;
- network monitoring;
- process listing or management;
- manual PWM presets, experimental fan-control helper and advanced or persistent fan curves;
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

## Local validation (Dell)

After checking out the candidate `work/first-prerelease-v0.1.0-alpha.1` branch,
run the project tests and source compilation in the local Linux environment:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m compileall -q src tests
```

Close any already-running Sentinelux tray instance, then launch the candidate
for a live GTK smoke test:

```bash
./scripts/run-dev.sh --debug
```

Verify the compact tray and per-core count (14 cores excluding the package on the Dell), that “Dettaglio sensori termici” opens a scrollable and updating window, and that thermal alerts/protection thresholds are unchanged. The **Ventole** page must be read-only, with no preset selector or apply button and no Polkit request. Smoke-test installed-user launcher and normal exit. The owner must report local command results and real desktop evidence before a PR, tag or GitHub prerelease. If an older experimental fan helper is still installed system-wide, remove it separately with `./scripts/uninstall-fan-helper.sh` (this release does not install it).

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
