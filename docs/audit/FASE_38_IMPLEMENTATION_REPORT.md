# FASE 38 — Implementation Report (Docs / Help Browser)

**Fecha:** 2026-07-26  
**Versión:** 0.30.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F37 Onboarding · F22 Chat (`search_docs`) · F35 Commands  
**Alcance:** docs list/content + panel Help — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Browser docs fail-closed | `workbench/docs_browser.py` |
| A1 | `GET /api/docs` · `GET /api/docs/content` | `api.py` + `server.py` |
| U1 | Panel Help/Docs | `static/js/panes/docs.js` |
| U2 | Shell / menu / API client | `shell.js` · `api.js` · `index.html` · CSS |
| C1 | Command `open.docs` | `commands.py` |
| T0 | Chat `search_docs` → ops/ | `chat/tools.py` |
| T1 | Tests F38 | `tests/unit/workbench/test_docs_f38.py` |
| T2 | Smoke F38 | `scripts/internal_audit_smoke.py` |
| D2 | Spec + DEC-082 + bump | `docs/FASE_38_DOCS_HELP.md` · `0.30.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Solo `docs/*.md` y `docs/ops/*.md`
- Path traversal / absolutos / otros subdirs → 400
- Preview HTML escapa markup crudo
- DEC-082

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_docs_f38.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Certificado externo `FASE_38_APPROVED.md`
- Lectura de `docs/audit/` u otros subárboles
