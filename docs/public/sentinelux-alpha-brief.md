# Sentinelux — first public alpha product brief

**Status:** candidate `v0.1.0-alpha.1`, not yet published.
**Python version:** `0.1.0a1`. **License:** GPL-3.0-or-later.
**Repository:** https://github.com/matteodurso88/sentinelux

## Italiano

**Sintesi:** Sentinelux è un monitor hardware per desktop Linux che rende
accessibili direttamente dalla tray CPU, RAM, swap, temperature della CPU e
letture delle ventole, quando disponibili. Il progetto fornisce notifiche
termiche configurabili e una protezione preventiva opzionale basata su
ibernazione o sospensione (disattivata per impostazione predefinita).

**Funzioni della prima alpha:** tray compatta, temperatura massima e
Package CPU, dettagli scorrevoli aggiornati, conteggio dei sensori per-core
senza contare il Package, letture RPM delle ventole in sola lettura,
preferenze persistenti, autostart XDG e snapshot JSON da terminale.

**Limitazioni:** la prima alpha non regola la velocità delle ventole e
non include preset PWM, helper privilegiato, pacchetto `.deb`, dashboard
storica, updater o compatibilità universale. Le metriche dipendono da
sensori esposti da driver e firmware. È un software alpha: le protezioni
hardware rimangono essenziali.

**Installazione:** da sorgente, con script per distribuzioni Debian-like;
la release GitHub e il tag saranno pubblicati solo dopo i test locali.

## English

**Summary:** Sentinelux is a Linux desktop hardware monitor that keeps
CPU load, memory pressure, swap, CPU temperature and available fan telemetry
at hand in an AppIndicator-compatible system tray. It supports configurable
thermal alerts and optional preventive sleep requests, off by default.

**First-alpha features:** compact tray; hottest CPU temperature and optional
package sensor; live scrollable sensor details; core sensor count excluding
package; read-only fan RPM telemetry; persistent preferences; per-user
autostart; and a one-shot JSON metrics command.

**Limitations:** no fan speed control or PWM presets, no privileged fan
helper, no `.deb` package, historical dashboards, auto-updater or universal
hardware compatibility. Sensors depend on the kernel and firmware. This is
alpha software, not a substitute for hardware/firmware thermal protection.

**Installation:** source-based for Debian-family Linux desktops; the tag
and GitHub prerelease are pending completion of the local release gate.

The technical release notes are in
[docs/releases/v0.1.0-alpha.1.md](../releases/v0.1.0-alpha.1.md).
