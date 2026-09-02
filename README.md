# Sentinelux

[Italiano](README.it.md) · [English](README.en.md) · [matt88.it](https://matt88.it)

**Sentinelux** is an open-source Linux desktop monitor that keeps CPU load, coherent RAM pressure, swap, CPU temperatures and available fan telemetry visible from the system tray. It also provides configurable thermal alerts, optional preventive sleep actions and per-user autostart.

**Sentinelux** è un monitor desktop open source per Linux che rende visibili dalla tray il carico CPU, la pressione RAM calcolata in modo coerente, lo swap, le temperature CPU e l’eventuale telemetria delle ventole. Include inoltre alert termici configurabili, azioni preventive opzionali e avvio automatico per utente.

> **Current status / Stato attuale:** `0.0.5` · pre-alpha · unreleased / non rilasciata

Sentinelux is created and maintained by **Matteo D'Urso** (`matteodurso88`) and is part of the public engineering work presented through **[matt88.it](https://matt88.it)**.

Sentinelux è creato e mantenuto da **Matteo D'Urso** (`matteodurso88`) e fa parte delle attività di engineering pubbliche presentate attraverso **[matt88.it](https://matt88.it)**.

## Documentation / Documentazione

- Detailed documentation in Italian: [README.it.md](README.it.md)
- Detailed documentation in English: [README.en.md](README.en.md)
- Public product dossier for matt88.it: [docs/public/sentinelux-matt88-dossier.md](docs/public/sentinelux-matt88-dossier.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- License: [GPL-3.0-or-later](LICENSE)

## What it demonstrates / Cosa dimostra

Sentinelux is also a compact, inspectable example of practical Linux desktop engineering:

Sentinelux è anche un esempio compatto e ispezionabile di engineering desktop Linux:

- Python-based desktop/system tooling;
- GTK 3 and AppIndicator-compatible tray integration;
- Linux hardware telemetry and system interfaces;
- thermal monitoring and user-configurable safety behavior;
- per-user installation and autostart workflows;
- bilingual public documentation and explicit project status.

## Quick start / Avvio rapido

```bash
./scripts/install-deps-debian.sh
./scripts/run-dev.sh --debug
```

Install for the current user / Installa per l’utente corrente:

```bash
./scripts/install-user.sh
~/.local/bin/sentinelux --debug
```

Print one JSON metrics snapshot / Stampa uno snapshot JSON:

```bash
./scripts/run-dev.sh --once
```

## Platform scope / Perimetro piattaforma

Sentinelux currently targets Debian-family desktop systems with Python 3.10+, GTK 3 and an AppIndicator-compatible tray. Hardware readings and privileged actions depend on what the kernel, firmware and desktop policy expose.

Sentinelux è attualmente rivolto a sistemi desktop della famiglia Debian con Python 3.10+, GTK 3 e una tray compatibile con AppIndicator. Letture hardware e azioni privilegiate dipendono da ciò che kernel, firmware e policy desktop rendono disponibile.

## Professional context / Contesto professionale

Sentinelux is one of the public open-source projects used to make engineering practices directly inspectable: implementation quality, documentation, Linux integration and maintainability.

Sentinelux è uno dei progetti open source pubblici utilizzati per rendere direttamente ispezionabili pratiche di engineering quali qualità dell'implementazione, documentazione, integrazione Linux e manutenibilità.

**Portfolio and case studies / Portfolio e case study:** [matt88.it](https://matt88.it)
