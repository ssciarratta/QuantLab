# FASE 60 — Implementation Report (i18n Scaffold)

**Fecha:** 2026-07-26  
**Versión:** 0.52.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F59 A11y Basics  
**Impl SHA:** _(pending commit)_  
**Alcance:** i18n scaffold es default + stub en — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Diccionario JS es + stub en | `static/js/i18n.js` |
| D2 | JSON static i18n | `static/i18n/es.json` · `en.json` |
| D3 | Python loader + payload | `workbench/i18n.py` |
| D4 | API GET `/api/i18n/{locale}` | `api.py` · `server.py` · OpenAPI |
| D5 | Shell apply locale + data-i18n | `shell.js` · `index.html` · settings pane |
| D6 | Spec + DEC-104 + bump | `docs/FASE_60_I18N.md` · **0.52.0** |
| D7 | Tests | `tests/unit/workbench/test_i18n_f60.py` |
| D8 | Implementation report | este doc |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_60_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-104
- `phases_summary == "F19–F60 INTERNAL"`
- About `version` ≡ `__version__` · **0.52.0**
- Default locale **es**

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
- Cobertura i18n 100% de paneles lab
- Certificado externo `FASE_60_APPROVED.md`
