# FASE 80 — Implementation Report (Custom Preset Save)

**Fecha:** 2026-07-26  
**Versión:** 0.72.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F79 Watchlist Import/Export JSON v0.71  
**Impl SHA:** `67fd498`  
**Alcance:** save/list/apply presets custom de sesión + UI — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Custom presets helpers | `workbench/presets.py` |
| D2 | API save + list/apply custom | `workbench/api.py` · `server.py` · `api_catalog.py` |
| D3 | Session `presets/` + ZIP | `session.py` · `session_zip.py` |
| D4 | QLApi + UI Inicio | `static/js/api.js` · `shell.js` · `index.html` · `i18n.js` |
| D5 | Spec + DEC-124 + bump | `docs/FASE_80_CUSTOM_PRESETS.md` · **0.72.0** |
| D6 | Suite | `tests/unit/workbench/test_custom_presets_f80.py` |
| D7 | Smoke F80 | `scripts/internal_audit_smoke.py` |
| D8 | Implementation report | este doc |
| D9 | Bundle default F19–F80 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_80_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-124
- `phases_summary == "F19–F80 INTERNAL"`
- About `version` ≡ `__version__` · **0.72.0**
- Custom path-safe; no shadow built-ins
- Apply custom restaura ventanas guardadas

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
- Certificado externo `FASE_80_APPROVED.md`
- Delete/rename preset UI
