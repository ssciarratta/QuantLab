# FASE 31 — Implementation Report (Feature Store Browser + Pipeline Runner)

**Fecha:** 2026-07-26  
**Versión:** 0.23.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F30 Universe/Catalog · F21 Lab · F5 Features  
**Alcance:** store browser read-only + pipeline demo persistido en sesión — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| S1 | Feature store browser | `workbench/feature_store_browser.py` |
| S2 | Session `features_dir` | `workbench/session.py` |
| L1 | `run_lab_features` + persist | `workbench/lab_services.py` |
| A1 | `GET /api/lab/features/store` | `api.py` + `server.py` |
| A2 | `POST /api/lab/features/run` (+ alias) | `api.py` + `server.py` |
| U1 | Panel Features enriquecido | `static/js/panes/features.js` |
| T1 | Tests F31 | `tests/unit/workbench/test_features_store_f31.py` |
| D1 | Spec + DEC-075 + bump | `docs/FASE_31_FEATURES_UI.md` · `0.23.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Persist solo sandbox sesión
- Store list read-only / empty-ok
- Nunca place_order venue
- DEC-075

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_features_store_f31.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Delete/overwrite feature versions desde UI
- Órdenes venue / auto-flip LIVE
