# Sentinelux

[Italiano](README.it.md) · [English](README.en.md)

**Sentinelux** is an open-source Linux desktop monitor that keeps CPU load, coherent RAM pressure, swap, CPU temperatures and available fan telemetry visible from the system tray. It also provides configurable thermal alerts, optional preventive sleep actions and per-user autostart.

**Sentinelux** è un monitor desktop open source per Linux che rende visibili dalla tray il carico CPU, la pressione RAM calcolata in modo coerente, lo swap, le temperature CPU e l’eventuale telemetria delle ventole. Include inoltre alert termici configurabili, azioni preventive opzionali e avvio automatico per utente.

> Current status / Stato attuale: **0.0.5 · pre-alpha · unreleased / non rilasciata**

- Detailed documentation in Italian: [README.it.md](README.it.md)
- Detailed documentation in English: [README.en.md](README.en.md)
- Public product dossier for matt88.it: [docs/public/sentinelux-matt88-dossier.md](docs/public/sentinelux-matt88-dossier.md)
- Contribution guide / Guida alla contribuzione: [CONTRIBUTING.md](CONTRIBUTING.md)
- Governance and merge policy / Governance e policy di merge: [GOVERNANCE.md](GOVERNANCE.md)
- Support and security / Supporto e sicurezza: [SUPPORT.md](SUPPORT.md) · [SECURITY.md](SECURITY.md)
- Code of conduct / Codice di condotta: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- License: [GPL-3.0-or-later](LICENSE)

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

Sentinelux currently targets Debian-family desktop systems with Python 3.10+, GTK 3 and an AppIndicator-compatible tray. Hardware readings and privileged actions depend on what the kernel, firmware and desktop policy expose.

Sentinelux è attualmente rivolto a sistemi desktop della famiglia Debian con Python 3.10+, GTK 3 e una tray compatibile con AppIndicator. Letture hardware e azioni privilegiate dipendono da ciò che kernel, firmware e policy desktop rendono disponibile.

## Contributing / Contribuire

The `main` branch is protected. Develop changes on a dedicated branch or fork, run the local checks, then open a pull request. Authorized maintainers decide whether to merge, request changes, or close the proposal.

Il branch `main` è protetto. Sviluppa le modifiche su un branch dedicato o su un fork, esegui le verifiche locali e apri una pull request. I maintainer autorizzati decidono se effettuare il merge, richiedere modifiche o chiudere la proposta.

See / Consulta [CONTRIBUTING.md](CONTRIBUTING.md) and [GOVERNANCE.md](GOVERNANCE.md).
