# Proceso — Sync GitHub al cerrar cada fase

**Problema resuelto:** commits locales sin `push` → Cursor/GitHub en el celular muestran el repo viejo.

## Flujo obligatorio (cierre de fase)

```
Implementar → tests/mypy/ruff verdes → certificado + RESUMEN
    → bash scripts/sync_phase_github.sh FASE_XX "Título"
    → verificar: git status = "up to date with origin/main"
```

## Comando

```bash
bash scripts/sync_phase_github.sh FASE_07 "Backtester 5B"
bash scripts/sync_phase_github.sh --status   # diagnóstico
```

## Checklist

- [ ] QA verde
- [ ] `docs/audit/FASE_XX_APPROVED.md` (si corresponde)
- [ ] `RESUMEN_PROYECTO.txt` actualizado
- [ ] Commit creado
- [ ] `git push origin main` OK
- [ ] En GitHub web / celular se ve el commit nuevo

## Regla Cursor

`.cursor/rules/phase-github-sync.mdc` (alwaysApply)

## Remote limpio (celular / Cursor)

- URL del remote: `https://github.com/ssciarratta/QuantLab.git` (**sin** token embebido).
- Credenciales: `gh auth` (keyring) con scope `repo`.
- CI workflow: si el PAT/OAuth no tiene scope `workflow`, no pushear `.github/workflows` (usar `docs/ci/ci.yml.example`).
- Si alguna vez hubo un token `ghp_` en la URL: revocarlo en  
  https://github.com/settings/tokens
