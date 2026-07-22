## Summary / Riepilogo

<!-- Explain what changes and why. Spiega cosa cambia e perché. -->

## Related issue / Issue collegata

<!-- Use: Closes #123, Fixes #123, or N/A. -->

## Change type / Tipo di modifica

- [ ] Bug fix / Correzione
- [ ] Feature / Funzionalità
- [ ] Documentation / Documentazione
- [ ] Tests / Test
- [ ] Refactor or maintenance / Refactoring o manutenzione

## Validation / Verifica

Commands executed / Comandi eseguiti:

```text
python3 -m compileall -q src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Result / Risultato:

<!-- Paste a concise result. Do not include personal data or full machine dumps. -->

## Safety, privacy, and privileges / Sicurezza, privacy e privilegi

- [ ] No new privileged operation / Nessuna nuova operazione privilegiata
- [ ] No new hardware write / Nessuna nuova scrittura hardware
- [ ] No new network or telemetry behavior / Nessun nuovo comportamento di rete o telemetria
- [ ] I described every relevant impact below / Ho descritto ogni impatto rilevante sotto

Impact and mitigations / Impatto e mitigazioni:

<!-- Required for /sys writes, pkexec, systemctl, sleep actions, notifications, logs, or local data. -->

## Hardware and compatibility / Hardware e compatibilità

<!-- Hardware, driver, distribution, desktop environment, X11/Wayland, unavailable-sensor behavior. Use N/A when not relevant. -->

## User-visible changes / Modifiche visibili

<!-- Add sanitized screenshots for GUI changes. Never include usernames, hostnames, private paths, tokens, or unrelated notifications. -->

## Checklist

- [ ] The change is focused and does not include unrelated work.
- [ ] La modifica è focalizzata e non contiene lavoro non correlato.
- [ ] Tests pass locally / I test locali sono superati.
- [ ] New behavior has tests or a documented reason why not.
- [ ] Il nuovo comportamento ha test o una motivazione documentata.
- [ ] Italian and English documentation remain consistent.
- [ ] La documentazione italiana e inglese resta coerente.
- [ ] Public behavior changes are reflected in README/changelog/dossier when relevant.
- [ ] Le modifiche pubbliche sono riportate in README/changelog/dossier quando necessario.
- [ ] No secrets or personal data are included / Nessun segreto o dato personale incluso.
- [ ] I read and accept CONTRIBUTING.md and CODE_OF_CONDUCT.md.
