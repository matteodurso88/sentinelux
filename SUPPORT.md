# Sentinelux Support / Supporto Sentinelux

[Italiano](#italiano) · [English](#english)

## Italiano

Sentinelux è un progetto open source pre-alpha mantenuto su base best effort. Non è attualmente disponibile un servizio di supporto commerciale né un tempo di risposta garantito.

### Dove chiedere aiuto

- **Bug riproducibile:** usa il modulo *Bug report / Segnalazione bug* nelle GitHub Issues.
- **Nuova funzione:** usa il modulo *Feature request / Proposta funzionalità*.
- **Domanda d'uso o compatibilità:** apri una issue scegliendo il modulo più vicino e spiega chiaramente che si tratta di una richiesta di supporto.
- **Vulnerabilità:** non usare una issue pubblica; segui [SECURITY.md](SECURITY.md).
- **Comportamento nella comunità:** segui [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Prima di aprire una issue:

1. cerca segnalazioni simili;
2. prova lo stato più recente supportato;
3. esegui `./scripts/run-dev.sh --once` quando il problema riguarda le metriche;
4. raccogli versione Sentinelux, distribuzione, desktop environment, X11/Wayland e modalità di installazione;
5. rimuovi dati personali, hostname, username, percorsi privati e token.

### Informazioni utili

Per problemi di tray, sensori o protezione termica indica:

- output di `sentinelux --version`;
- distribuzione e versione;
- desktop environment e sessione X11/Wayland;
- comportamento atteso e osservato;
- passaggi di riproduzione;
- output essenziale di `--debug` o `--once`;
- presenza o assenza dei file rilevanti in `/sys/class/hwmon` o `/sys/class/thermal`;
- eventuali messaggi di `systemd-logind`, senza dati sensibili.

L'assenza di un sensore o di un controllo hardware può essere una limitazione del kernel, del driver, del firmware o del dispositivo e non sempre può essere risolta da Sentinelux.

---

## English

Sentinelux is a pre-alpha open-source project maintained on a best-effort basis. Commercial support and guaranteed response times are not currently available.

### Where to ask for help

- **Reproducible bug:** use the *Bug report / Segnalazione bug* GitHub issue form.
- **New feature:** use the *Feature request / Proposta funzionalità* form.
- **Usage or compatibility question:** open an issue using the closest form and state clearly that it is a support request.
- **Vulnerability:** do not use a public issue; follow [SECURITY.md](SECURITY.md).
- **Community conduct:** follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Before opening an issue:

1. search for similar reports;
2. test the latest supported state;
3. run `./scripts/run-dev.sh --once` when the problem concerns metrics;
4. collect the Sentinelux version, distribution, desktop environment, X11/Wayland session, and installation method;
5. remove personal data, hostnames, usernames, private paths, and tokens.

### Useful information

For tray, sensor, or thermal-protection problems, include:

- `sentinelux --version` output;
- distribution and version;
- desktop environment and X11/Wayland session;
- expected and observed behavior;
- reproduction steps;
- essential `--debug` or `--once` output;
- presence or absence of relevant files under `/sys/class/hwmon` or `/sys/class/thermal`;
- relevant `systemd-logind` messages, without sensitive data.

A missing sensor or hardware control may be a kernel, driver, firmware, or device limitation and cannot always be fixed by Sentinelux.
