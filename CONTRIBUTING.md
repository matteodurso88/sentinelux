# Contributing to Sentinelux / Contribuire a Sentinelux

[Italiano](#italiano) · [English](#english)

Sentinelux accepts contributions through GitHub issues and pull requests. The `main` branch is protected: changes must be developed on a dedicated branch and reviewed through a pull request before they can become part of the official codebase.

Sentinelux accetta contributi tramite issue e pull request GitHub. Il branch `main` è protetto: le modifiche devono essere sviluppate su un branch dedicato e revisionate tramite pull request prima di entrare nel codice ufficiale.

---

## Italiano

### Prima di iniziare

- Leggi il [Codice di condotta](CODE_OF_CONDUCT.md).
- Cerca tra le issue esistenti per evitare duplicati.
- Apri prima una issue per cambiamenti estesi, nuove integrazioni hardware, modifiche ai privilegi o variazioni dell'architettura.
- Le correzioni piccole e chiaramente delimitate possono essere proposte direttamente con una pull request.
- Non inserire credenziali, token, indirizzi privati, nomi host, dump completi della macchina o altri dati personali.

Le vulnerabilità non devono essere riportate in una issue pubblica: consulta [SECURITY.md](SECURITY.md).

### Modello di contribuzione

Contributore esterno:

1. crea un fork di `matteodurso88/sentinelux`;
2. crea un branch nel proprio fork;
3. esegue modifiche, test e commit;
4. pubblica il branch sul fork;
5. apre una pull request verso `matteodurso88/sentinelux:main`.

Collaboratore con accesso diretto:

1. aggiorna `main`;
2. crea un branch nel repository;
3. pubblica il branch;
4. apre una pull request verso `main`.

Il push diretto su `main` non fa parte del workflow accettato. I maintainer autorizzati decidono se eseguire il merge, richiedere modifiche o chiudere la proposta. Consulta [GOVERNANCE.md](GOVERNANCE.md).

### Preparazione dell'ambiente

Sentinelux è attualmente sviluppato per desktop Linux della famiglia Debian.

```bash
./scripts/install-deps-debian.sh
./scripts/run-dev.sh --debug
```

Per ottenere uno snapshot senza avviare la GUI:

```bash
./scripts/run-dev.sh --once
```

### Branch

Usa nomi brevi e descrittivi:

```text
feat/nome-funzionalita
fix/nome-correzione
docs/argomento
test/argomento
refactor/argomento
chore/argomento
```

Esempio:

```bash
git switch main
git pull --ff-only
git switch -c feat/battery-telemetry
```

### Commit

Usa messaggi imperativi e delimitati. Il progetto adotta una convenzione compatibile con Conventional Commits:

```text
feat: add battery telemetry
fix: handle missing thermal zone
docs: document contribution workflow
test: cover memory presentation
refactor: isolate sensor selection
chore: update development tooling
```

Un commit deve:

- rappresentare un cambiamento coerente;
- non contenere file generati o dati della macchina non necessari;
- lasciare la suite di test in uno stato superato;
- mantenere sincronizzata la documentazione italiana e inglese quando cambia il comportamento pubblico.

### Verifiche locali

Prima di aprire la pull request esegui:

```bash
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Per modifiche all'interfaccia, allega uno screenshot sanitizzato quando utile. Per modifiche hardware o di sistema, descrivi anche l'hardware, il driver, i file `/sys` coinvolti e il comportamento in assenza del sensore.

### Requisiti per modifiche hardware e privilegiate

Le modifiche che leggono o scrivono dati hardware devono rispettare questi principi:

- funzionamento in sola lettura come impostazione predefinita;
- scritture sempre esplicite e opt-in;
- nessuna applicazione automatica di preset rischiosi all'accesso;
- convalida rigorosa di percorsi, valori e capacità del sistema;
- privilegi limitati all'operazione strettamente necessaria;
- fallback sicuro quando il kernel o il firmware non espongono il controllo;
- tentativo di ripristino dello stato originale quando una modifica è temporanea;
- test che non eseguano realmente sospensione, ibernazione o scritture PWM;
- documentazione chiara dei rischi e delle limitazioni.

Non provocare intenzionalmente surriscaldamento, arresti termici o perdita di dati per verificare una patch.

### Pull request

La pull request deve includere:

- problema affrontato e motivazione;
- riepilogo delle modifiche;
- issue collegata, quando presente;
- comandi di test eseguiti e risultato;
- impatto su sicurezza, privacy, privilegi e hardware;
- screenshot per modifiche visibili;
- note su compatibilità e limitazioni;
- aggiornamento di README, changelog o dossier quando cambia il comportamento pubblico.

Mantieni la PR focalizzata. Modifiche non correlate devono essere separate.

Il maintainer può richiedere modifiche, test aggiuntivi o una riduzione dello scope. L'apertura di una PR non garantisce il merge.

### Licenza dei contributi

Inviando un contributo dichiari di avere il diritto di pubblicarlo e accetti che venga distribuito con la licenza del progetto, **GPL-3.0-or-later**. Sentinelux non richiede attualmente un Contributor License Agreement separato.

---

## English

### Before you start

- Read the [Code of Conduct](CODE_OF_CONDUCT.md).
- Search existing issues to avoid duplicates.
- Open an issue before large changes, new hardware integrations, privilege changes, or architectural work.
- Small, clearly scoped fixes may be submitted directly as pull requests.
- Do not include credentials, tokens, private addresses, hostnames, full machine dumps, or other personal data.

Do not report vulnerabilities in a public issue. Follow [SECURITY.md](SECURITY.md).

### Contribution model

External contributor:

1. fork `matteodurso88/sentinelux`;
2. create a branch in the fork;
3. implement, test, and commit the change;
4. push the branch to the fork;
5. open a pull request targeting `matteodurso88/sentinelux:main`.

Direct collaborator:

1. update `main`;
2. create a repository branch;
3. push the branch;
4. open a pull request targeting `main`.

Direct pushes to `main` are not part of the accepted workflow. Authorized maintainers decide whether to merge, request changes, or close a proposal. See [GOVERNANCE.md](GOVERNANCE.md).

### Development setup

Sentinelux currently targets Debian-family Linux desktops.

```bash
./scripts/install-deps-debian.sh
./scripts/run-dev.sh --debug
```

Print one snapshot without starting the GUI:

```bash
./scripts/run-dev.sh --once
```

### Branches

Use short, descriptive names:

```text
feat/feature-name
fix/bug-name
docs/topic
test/topic
refactor/topic
chore/topic
```

Example:

```bash
git switch main
git pull --ff-only
git switch -c feat/battery-telemetry
```

### Commits

Use imperative, scoped messages following a Conventional Commits-compatible style:

```text
feat: add battery telemetry
fix: handle missing thermal zone
docs: document contribution workflow
test: cover memory presentation
refactor: isolate sensor selection
chore: update development tooling
```

A commit should:

- represent one coherent change;
- exclude unnecessary generated or machine-specific files;
- leave the test suite passing;
- keep Italian and English documentation aligned when public behavior changes.

### Local checks

Run before opening a pull request:

```bash
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

For UI changes, attach a sanitized screenshot when useful. For hardware or system changes, describe the hardware, driver, relevant `/sys` files, and behavior when the sensor is unavailable.

### Hardware and privileged changes

Changes that read or write hardware state must follow these principles:

- read-only behavior by default;
- explicit opt-in for every write;
- no automatic risky preset at login;
- strict validation of paths, values, and system capabilities;
- privileges limited to the smallest required operation;
- safe fallback when the kernel or firmware does not expose control;
- restoration of the original state when a change is session-scoped;
- tests that never perform real suspension, hibernation, or PWM writes;
- clear documentation of risks and limitations.

Do not intentionally trigger overheating, thermal shutdown, or data loss to validate a patch.

### Pull requests

A pull request should include:

- the problem and motivation;
- a concise change summary;
- a linked issue when available;
- test commands and results;
- security, privacy, privilege, and hardware impact;
- screenshots for visible changes;
- compatibility notes and known limitations;
- README, changelog, or dossier updates when public behavior changes.

Keep the pull request focused. Unrelated changes should be split.

The maintainer may request revisions, additional tests, or a smaller scope. Opening a pull request does not guarantee merge.

### Contribution license

By submitting a contribution, you confirm that you have the right to publish it and agree that it will be distributed under the project license, **GPL-3.0-or-later**. Sentinelux does not currently require a separate Contributor License Agreement.
