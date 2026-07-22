# Sentinelux Governance / Governance di Sentinelux

[Italiano](#italiano) · [English](#english)

## Italiano

### Modello del progetto

Sentinelux è un progetto open source guidato dal maintainer. Il maintainer di riferimento è **@matteodurso88**.

Il codice ufficiale è quello pubblicato nel branch protetto `main` del repository `matteodurso88/sentinelux`. Fork, branch e patch esterne sono proposte finché non vengono integrate tramite pull request.

### Autorità e responsabilità

Il maintainer di riferimento:

- definisce direzione, scope e priorità;
- valuta issue e pull request;
- può richiedere modifiche o test aggiuntivi;
- decide merge, rifiuto o chiusura delle proposte;
- assegna o revoca ruoli e permessi del repository;
- coordina release, advisory e modifiche alle policy.

L'accesso `write`, `maintain` o `admin` può essere concesso a collaboratori fidati. Tale accesso non sostituisce il workflow tramite pull request e non attribuisce automaticamente autorità decisionale indipendente, salvo delega esplicita.

### Workflow decisionale

Le decisioni tecniche considerano:

- coerenza con lo scope di Sentinelux;
- beneficio per gli utenti;
- manutenibilità e qualità del codice;
- sicurezza di operazioni hardware e privilegiate;
- compatibilità con sistemi realmente verificati;
- presenza di test e documentazione;
- costo di manutenzione futuro.

Il consenso è preferito, ma il maintainer di riferimento conserva la decisione finale. Una proposta può essere rifiutata anche se tecnicamente valida quando aumenta rischi o complessità oltre il valore previsto.

### Branch e merge

- `main` è protetto.
- Il push diretto su `main` non è il workflow ammesso.
- Le modifiche entrano tramite pull request.
- Force push e cancellazione di `main` non sono consentiti.
- Le conversazioni irrisolte devono essere chiuse prima del merge.
- Il repository preferisce una cronologia lineare.
- `CODEOWNERS` indica il maintainer di riferimento come responsabile predefinito e consente a GitHub di richiederne automaticamente la review.

Le impostazioni tecniche del repository possono diventare più restrittive senza modificare questa policy.

### Contributori e maintainer

Una contribuzione accettata non conferisce automaticamente accesso al repository. L'eventuale promozione a collaboratore o maintainer considera continuità, qualità delle review, affidabilità, conoscenza del progetto e rispetto delle policy.

### Modifiche alla governance

Le modifiche a questo documento seguono lo stesso processo delle altre modifiche: branch dedicato, pull request e decisione del maintainer di riferimento.

---

## English

### Project model

Sentinelux is a maintainer-led open-source project. The maintainer of record is **@matteodurso88**.

The official code is the content of the protected `main` branch in `matteodurso88/sentinelux`. Forks, branches, and external patches remain proposals until merged through a pull request.

### Authority and responsibilities

The maintainer of record:

- defines direction, scope, and priorities;
- evaluates issues and pull requests;
- may request revisions or additional tests;
- decides whether to merge, reject, or close proposals;
- grants or revokes repository roles and permissions;
- coordinates releases, advisories, and policy changes.

`write`, `maintain`, or `admin` access may be granted to trusted collaborators. Such access does not replace the pull-request workflow and does not automatically grant independent decision authority unless explicitly delegated.

### Decision process

Technical decisions consider:

- alignment with Sentinelux scope;
- user benefit;
- maintainability and code quality;
- safety of hardware and privileged operations;
- compatibility with systems that have actually been verified;
- tests and documentation;
- future maintenance cost.

Consensus is preferred, but the maintainer of record retains final authority. A technically valid proposal may still be declined when its risk or complexity exceeds its expected value.

### Branches and merge

- `main` is protected.
- Direct pushes to `main` are not an accepted workflow.
- Changes enter through pull requests.
- Force pushes and deletion of `main` are not allowed.
- Unresolved conversations must be resolved before merge.
- The repository prefers linear history.
- `CODEOWNERS` identifies the maintainer of record as the default owner and allows GitHub to request that review automatically.

Technical repository settings may become more restrictive without changing this policy.

### Contributors and maintainers

An accepted contribution does not automatically grant repository access. Promotion to collaborator or maintainer may consider sustained participation, review quality, reliability, project knowledge, and compliance with project policies.

### Governance changes

Changes to this document follow the same process as other changes: dedicated branch, pull request, and a decision by the maintainer of record.
