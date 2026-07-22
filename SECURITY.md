# Security Policy / Policy di sicurezza

[Italiano](#italiano) · [English](#english)

## Italiano

### Versioni supportate

Sentinelux è in stato pre-alpha e non dispone ancora di release pubbliche. La manutenzione di sicurezza riguarda soltanto lo stato più recente del branch `main`. Snapshot, fork o installazioni precedenti non ricevono garanzie di backport.

| Versione | Supporto di sicurezza |
|---|---|
| Ultimo `main` | Best effort |
| Snapshot precedenti | Non supportati formalmente |
| Fork di terze parti | Gestiti dai rispettivi proprietari |

### Segnalazione di una vulnerabilità

Non aprire una issue pubblica con dettagli tecnici sfruttabili.

1. Controlla la scheda **Security** del repository e usa **Report a vulnerability** quando disponibile.
2. Se il reporting privato non è disponibile, apri una issue pubblica intitolata `Security contact request` senza includere dettagli, log, proof of concept o dati della macchina.
3. Il maintainer stabilirà un canale privato per ricevere il rapporto completo.

Il rapporto privato dovrebbe includere:

- componente e versione/commit interessati;
- impatto potenziale;
- prerequisiti e ambiente;
- passaggi minimi per riprodurre;
- eventuale proof of concept non distruttiva;
- mitigazioni note;
- indicazione dei dati che possono essere pubblicati.

Non esiste ancora un SLA formale. Il maintainer confermerà la ricezione quando possibile, valuterà il rapporto e coordinerà correzione e divulgazione.

### Ambiti sensibili

Sentinelux interagisce con metriche locali, `/sys`, `systemd-logind`, `systemctl` e, quando installato, un helper privilegiato per PWM. Sono particolarmente rilevanti:

- convalida di percorsi e valori passati all'helper;
- escalation di privilegi o uso improprio di `pkexec`;
- esecuzione non richiesta di sospensione o ibernazione;
- scritture PWM non autorizzate o non ripristinate;
- esposizione di dati locali tramite log, issue o screenshot;
- comandi costruiti da input non fidato.

Non testare una vulnerabilità provocando surriscaldamento, perdita di dati o arresti termici reali.

### Divulgazione

La divulgazione pubblica dovrebbe avvenire dopo una correzione o una mitigazione concordata. Il maintainer può pubblicare una advisory, attribuire il ricercatore se richiesto e indicare versioni interessate, impatto e aggiornamento consigliato.

---

## English

### Supported versions

Sentinelux is pre-alpha and does not yet have public releases. Security maintenance applies only to the latest state of the `main` branch. Older snapshots, forks, and installations do not receive guaranteed backports.

| Version | Security support |
|---|---|
| Latest `main` | Best effort |
| Older snapshots | Not formally supported |
| Third-party forks | Managed by their owners |

### Reporting a vulnerability

Do not open a public issue containing exploitable technical details.

1. Check the repository **Security** tab and use **Report a vulnerability** when available.
2. If private reporting is unavailable, open a public issue titled `Security contact request` without details, logs, proof of concept, or machine data.
3. The maintainer will establish a private channel for the complete report.

A private report should include:

- affected component and version/commit;
- potential impact;
- prerequisites and environment;
- minimal reproduction steps;
- a non-destructive proof of concept when relevant;
- known mitigations;
- which information may be published.

There is no formal response SLA yet. The maintainer will acknowledge the report when possible, assess it, and coordinate remediation and disclosure.

### Sensitive areas

Sentinelux interacts with local metrics, `/sys`, `systemd-logind`, `systemctl`, and an optional privileged PWM helper. Relevant risks include:

- path and value validation in the helper;
- privilege escalation or misuse of `pkexec`;
- unintended suspension or hibernation;
- unauthorized or unrestored PWM writes;
- exposure of local data through logs, issues, or screenshots;
- commands built from untrusted input.

Do not validate a vulnerability by causing overheating, data loss, or a real thermal shutdown.

### Disclosure

Public disclosure should follow an agreed fix or mitigation. The maintainer may publish an advisory, credit the reporter when requested, and document affected versions, impact, and recommended updates.
