# FASE 64 — Implementation Report (Backups Panel UI)

**Fecha:** 2026-07-26  
**Versión:** 0.56.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F63 Session Auto-Backup  
**Alcance:** Panel UI Backups + POST `/api/backups/run` + menú + palette — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Panel Backups | `static/js/panes/backups.js` |
| D2 | API POST run | `api.py` · `server.py` · `api_catalog.py` |
| D3 | Menú Inicio + shell opener | `index.html` · `shell.js` |
| D4 | Command palette | `commands.py` · `open.backups` |
| D5 | i18n + CSS | `i18n.js` · `es.json`/`en.json` · `workbench.css` |
| D6 | Spec + DEC-108 + bump | `docs/FASE_64_BACKUPS_UI.md` · **0.56.0** |
| D7 | Tests UI + HTTP | `tests/unit/workbench/test_backups_ui_f64.py` |
| D8 | Implementation report | este doc |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_64_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-108
- `phases_summary == "F19–F64 INTERNAL"`
- About `version` ≡ `__version__` · **0.56.0**
- Reusa allowlist F39 + zip-slip via `run_auto_backup`

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff check src/quantlab tests scripts
uv run mypy --strict src/quantlab
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Certificado externo `FASE_64_APPROVED.md`
- Restore one-click / download desde panel
