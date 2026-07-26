# FASE 79 — Implementation Report (Watchlist Import/Export JSON)

**Fecha:** 2026-07-26  
**Versión:** 0.71.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F78 Milestone Freeze Docs v0.70  
**Impl SHA:** _(tip post-commit)_  
**Alcance:** export/import JSON watchlist + UI Universe — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Helpers export/import | `workbench/watchlist.py` |
| D2 | API export/import | `workbench/api.py` · `server.py` · `api_catalog.py` |
| D3 | QLApi + UI Universe | `static/js/api.js` · `panes/universe.js` |
| D4 | Spec + DEC-123 + bump | `docs/FASE_79_WATCHLIST_IO.md` · **0.71.0** |
| D5 | Suite | `tests/unit/workbench/test_watchlist_io_f79.py` |
| D6 | Smoke F79 | `scripts/internal_audit_smoke.py` |
| D7 | Implementation report | este doc |
| D8 | Bundle default F19–F79 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_79_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-123
- `phases_summary == "F19–F79 INTERNAL"`
- About `version` ≡ `__version__` · **0.71.0**
- Export Content-Disposition attachment JSON canónico
- Import merge/replace fail-closed

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
- Certificado externo `FASE_79_APPROVED.md`
- Named multi-watchlists
