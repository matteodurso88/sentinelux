# Sentinelux

[English documentation](README.en.md) · [README bilingue](README.md)

Sentinelux è un monitor hardware open source per desktop Linux, progettato per offrire informazioni essenziali direttamente nella tray: carico CPU, memoria RAM, swap, temperature CPU e ventole quando il kernel le espone. L’obiettivo attuale è fornire visibilità immediata e alert termici configurabili senza trasformare l’applicazione in una dashboard invasiva.

> **Stato:** [prima release pubblica `v0.1.0-alpha.1`](https://github.com/matteodurso88/sentinelux/releases/tag/v0.1.0-alpha.1) (`0.1.0a1` per Python), alpha pubblicata il 10 ottobre 2026. Nessun pacchetto `.deb` disponibile.

## Funzioni disponibili

- tray icon con etichetta della temperatura più alta o del carico CPU;
- menu tray compatto con CPU, RAM, swap, temperatura massima CPU, sensore package quando disponibile e ventole;
- finestra GTK scorrevole con il dettaglio completo e aggiornato dei sensori termici CPU; conteggio core separato dal Package e numerazione progressiva, con etichette hardware originali nei tooltip;
- RAM calcolata tramite memoria disponibile, con pattern coerente:
  `▣ RAM · 61.4% · 2.3 GiB / 3.8 GiB · disp. 1.4 GiB`;
- selezione del gruppo di sensori CPU più plausibile e uso del valore più caldo per la policy termica;
- notifiche di attenzione, criticità, promemoria e recupero;
- soglie, isteresi, intervalli e tipi di alert configurabili;
- preferenze persistenti in `~/.config/sentinelux/config.json`;
- avvio automatico XDG attivabile dalle preferenze;
- protezione termica preventiva opzionale tramite ibernazione o sospensione;
- visualizzazione in sola lettura del trip point `critical` più basso esposto dal kernel;
- monitoraggio delle ventole tramite `hwmon` in sola lettura (RPM, PWM e modalità se esposti); nessun controllo manuale;
- snapshot JSON da riga di comando con `--once`;
- installazione e disinstallazione per singolo utente.

## Requisiti confermati

Sentinelux è stato costruito per desktop Linux della famiglia Debian e richiede:

- Python 3.10 o successivo;
- GTK 3 e PyGObject;
- `psutil`;
- Ayatana AppIndicator oppure AppIndicator legacy;
- libnotify;
- `systemd-logind`, `busctl` e `systemctl` per le azioni preventive;
- una sessione desktop con tray AppIndicator compatibile.

La validazione locale disponibile riguarda un ambiente Xfce/X11. Distribuzione e versione esatte, Wayland e architetture CPU diverse non sono ancora formalmente verificate.

## Avvio in modalità sviluppo

```bash
./scripts/install-deps-debian.sh
./scripts/run-dev.sh --debug
```

Il comando crea il file di configurazione al primo avvio. Per una singola lettura senza GUI:

```bash
./scripts/run-dev.sh --once
```

Opzioni utili:

```text
--version
--once
--debug
--no-notifications
--warning-temp CELSIUS
--critical-temp CELSIUS
--interval SECONDS
```

## Installazione per l’utente corrente

```bash
./scripts/install-user.sh
~/.local/bin/sentinelux --debug
```

L’installazione copia l’applicazione in:

```text
~/.local/share/sentinelux
~/.local/bin/sentinelux
~/.local/share/applications/io.matt88.Sentinelux.desktop
```

L’avvio automatico può essere gestito da **Preferenze → Avvio** oppure dal terminale:

```bash
./scripts/enable-autostart.sh
./scripts/disable-autostart.sh
```

## Configurazione

La finestra **Preferenze** contiene le schede:

- **Monitoraggio** — intervallo, soglia di attenzione, soglia critica, isteresi e promemoria;
- **Alert** — interruttore generale e tipi di notifica;
- **Protezione** — azione preventiva, soglia, persistenza, isteresi e trip point kernel in sola lettura;
- **Ventole** — telemetria `hwmon` in sola lettura, senza preset manuali;
- **Avvio** — autostart XDG.

La configurazione viene salvata atomicamente in:

```text
~/.config/sentinelux/config.json
```

## Protezione termica preventiva

La protezione è disattivata per impostazione predefinita. Quando viene abilitata, Sentinelux richiede che la temperatura più alta resti sopra la soglia configurata per un tempo minimo. Se la temperatura rientra sotto la soglia meno l’isteresi, l’azione pendente viene annullata.

Azioni disponibili:

- ibernazione;
- sospensione.

Sentinelux interroga `systemd-logind` per verificare se l’azione è disponibile e autorizzata. Non modifica le soglie del kernel, del BIOS, del firmware o dell’hardware. La soglia `critical` mostrata nella GUI è una lettura di `/sys/class/thermal` e può non rappresentare tutte le protezioni presenti nella macchina.

## Ventole: telemetria in sola lettura

Sentinelux legge da `/sys/class/hwmon` i valori RPM e, se presenti, PWM e modalità del driver. **Non modifica i valori PWM, la velocità delle ventole o i profili termici del firmware.** La presenza di attributi PWM leggibili non garantisce che il firmware consenta il controllo manuale. Su alcuni Dell (`dell_ddv` e `dell_smm`) più canali `hwmon` possono descrivere una sola ventola fisica.

I preset sperimentali non fanno parte di `v0.1.0-alpha.1`: l’helper privilegiato e lo script di installazione sono esclusi. Se ne avevi installato uno da una precedente versione sperimentale, puoi rimuoverlo volontariamente con `./scripts/uninstall-fan-helper.sh`.

## Dati, rete e privilegi

Durante il normale monitoraggio Sentinelux legge metriche locali tramite `psutil`, `/sys/class/hwmon` e `/sys/class/thermal`. Non contiene telemetria, sincronizzazione cloud o chiamate di rete runtime.

I privilegi amministrativi non sono richiesti per tray, metriche, configurazione o installazione utente. Sono richiesti soltanto per:

- installare dipendenze di sistema;
- eseguire sospensione o ibernazione secondo le policy di sistema.

## Test

Esecuzione locale:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Ultimo gate storico: **42 test superati il 22 luglio 2026** su una build precedente. La candidata `v0.1.0-alpha.1` richiede nuovi test e smoke test locali prima della release.

## Limitazioni attuali

Non sono ancora implementati:

- dashboard completa con dettagli storici;
- batteria e alimentazione;
- storage e SMART;
- rete;
- elenco e gestione processi;
- grafici;
- localizzazione runtime inglese;
- pacchetto `.deb`, repository APT e aggiornamenti automatici;
- asset grafici e screenshot pubblici sanitizzati.

## Aggiornamento e rimozione

Non esiste ancora un sistema di aggiornamento integrato. Dopo aver aggiornato i sorgenti, rieseguire:

```bash
./scripts/install-user.sh
```

Per disinstallare:

```bash
./scripts/uninstall-user.sh
```

Lo script conserva intenzionalmente `~/.config/sentinelux`. Un eventuale helper ventole installato da una precedente branch sperimentale va rimosso separatamente con `./scripts/uninstall-fan-helper.sh`.

## Contribuire

Il repository è pubblico e il tracker indicato dal progetto è:

`https://github.com/matteodurso88/sentinelux/issues`

Non è ancora disponibile una guida formale alla contribuzione. Prima di una modifica estesa è opportuno aprire una issue descrittiva.

## Licenza

Sentinelux è distribuito con licenza **GPL-3.0-or-later**. Consulta [LICENSE](LICENSE).
