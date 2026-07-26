# FASE 81 — Implementation Report (Custom Preset Delete)

**Fecha:** 2026-07-26  
**Versión:** 0.73.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F80 Custom Preset Save v0.72  
**Impl SHA:** `2975729`  
**Alcance:** DELETE custom presets + UI — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | `delete_custom_preset` | `workbench/presets.py` |
| D2 | API DELETE + `do_DELETE` | `workbench/api.py` · `server.py` · `api_catalog.py` |
| D3 | QLApi + UI × | `static/js/api.js` · `shell.js` · `i18n.js` · `workbench.css` |
| D4 | Spec + DEC-125 + bump | `docs/FASE_81_PRESET_DELETE.md` · **0.73.0** |
| D5 | Suite | `tests/unit/workbench/test_preset_delete_f81.py` |
| D6 | Smoke F81 | `scripts/internal_audit_smoke.py` |
| D7 | Implementation report | este doc |
| D8 | Bundle default F19–F81 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_81_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-125
- `phases_summary == "F19–F81 INTERNAL"`
- About `version` ≡ `__version__` · **0.73.0**
- Built-ins `research|trading_paper|ops` no borrables
- DELETE custom elimina `presets/{name}.json`

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
- Certificado externo `FASE_81_APPROVED.md`
- Rename preset UI
