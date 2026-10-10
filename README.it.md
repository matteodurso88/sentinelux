# Sentinelux

[English documentation](README.en.md) · [README bilingue](README.md)

Sentinelux è un monitor hardware open source per desktop Linux, progettato per offrire informazioni essenziali direttamente nella tray: carico CPU, memoria RAM, swap, temperature CPU e ventole quando il kernel le espone. L’obiettivo attuale è fornire visibilità immediata e alert termici configurabili senza trasformare l’applicazione in una dashboard invasiva.

> **Stato:** versione `0.0.5`, pre-alpha, non ancora pubblicata come release o pacchetto `.deb`.

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
- rilevamento ventole tramite `hwmon`, con controllo PWM solo quando il canale è verificabile;
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
- `pkexec` soltanto per eventuali preset PWM;
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
- **Ventole** — telemetria `hwmon` e preset PWM quando supportati;
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

## Ventole e preset PWM

Sentinelux legge i canali esposti in `/sys/class/hwmon`. La pagina resta in sola lettura quando il sistema non espone contemporaneamente:

- tachimetro `fanN_input`;
- valore `pwmN`;
- modalità `pwmN_enable`.

Per autorizzare i preset su hardware compatibile:

```bash
./scripts/install-fan-helper.sh
```

Preset di sessione:

- Automatico;
- Silenzioso · 55%;
- Bilanciato · 70%;
- Prestazioni · 85%;
- Massimo · 100%.

Non esiste un preset a velocità zero. Sentinelux verifica il feedback RPM dopo una modifica manuale e tenta di ripristinare lo stato iniziale alla chiusura normale. I preset non sono persistenti e non vengono applicati all’accesso. Per rimuovere l’helper:

```bash
./scripts/uninstall-fan-helper.sh
```

## Dati, rete e privilegi

Durante il normale monitoraggio Sentinelux legge metriche locali tramite `psutil`, `/sys/class/hwmon` e `/sys/class/thermal`. Non contiene telemetria, sincronizzazione cloud o chiamate di rete runtime.

I privilegi amministrativi non sono richiesti per tray, metriche, configurazione o installazione utente. Sono richiesti soltanto per:

- installare dipendenze di sistema;
- installare o rimuovere l’helper ventole;
- applicare preset PWM tramite `pkexec`, quando supportati;
- eseguire sospensione o ibernazione secondo le policy di sistema.

## Test

Esecuzione locale:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Stato verificato il 22 luglio 2026: **42 test unitari superati**. Non è ancora presente una pipeline CI/CD nel repository.

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

Lo script conserva intenzionalmente `~/.config/sentinelux`. L’helper ventole, se installato, va rimosso separatamente.

## Contribuire

Il repository è pubblico e il tracker indicato dal progetto è:

`https://github.com/matteodurso88/sentinelux/issues`

Non è ancora disponibile una guida formale alla contribuzione. Prima di una modifica estesa è opportuno aprire una issue descrittiva.

## Licenza

Sentinelux è distribuito con licenza **GPL-3.0-or-later**. Consulta [LICENSE](LICENSE).
