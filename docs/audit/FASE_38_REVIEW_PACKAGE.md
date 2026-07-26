# FASE 38 — Review Package INTERNAL (Docs / Help Browser)

**Fecha:** 2026-07-26  
**Versión código (impl F38):** 0.30.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** browser read-only vía `workbench/docs_browser.py` limitado a `docs/*.md` y `docs/ops/*.md`; API `GET /api/docs` + `GET /api/docs/content?path=` con path traversal fail-closed; panel Help/Docs (buscar + preview HTML escapado | pre); chat `search_docs` reutiliza el mismo listado (incluye ops/). DEC-082.

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Browser fail-closed | `workbench/docs_browser.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Panel Docs JS | `static/js/panes/docs.js` |
| A4 | Shell / menu / CSS | `shell.js` · `api.js` · `index.html` · CSS |
| A5 | Spec | `docs/FASE_38_DOCS_HELP.md` |
| A6 | Implementation report | `docs/audit/FASE_38_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-082 | `learning/decisiones.txt` |
| A8 | Suite F38 | `tests/unit/workbench/test_docs_f38.py` |
| A9 | Version 0.30.0 | `pyproject.toml` |
| A10 | Impl SHA | `becd116` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.30.0
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

LIVE flip · auth WAN · browser E2E · certificado externo `FASE_38_APPROVED.md` · servir `docs/audit/`
