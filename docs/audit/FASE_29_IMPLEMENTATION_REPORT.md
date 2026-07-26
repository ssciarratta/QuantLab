# FASE 29 — Implementation Report (Report Viewer + Metrics History)

**Fecha:** 2026-07-26  
**Versión:** 0.21.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F28 Layout/Journal · F21 Lab panels · F8 ReportGenerator  
**Alcance:** persistencia reports lab + API + panel UI — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| R1 | Persist MetricsResult/summary + HTML | `workbench/reports.py` |
| R2 | Session `reports_dir` | `workbench/session.py` |
| R3 | Backtest wire `reports_dir` | `lab_services.run_lab_backtest` |
| A1 | `GET /api/lab/reports` + `/{id}` | `api.py` + `server.py` |
| U1 | Panel Reports | `static/js/panes/reports.js` + shell/index/api/css |
| T1 | Tests F29 | `tests/unit/workbench/test_reports_f29.py` |
| D1 | Spec + DEC-073 + bump | `docs/FASE_29_REPORTS.md` · `0.21.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- `report_id` fail-closed (charset / sandbox)
- Persistencia solo tras backtest lab exitoso
- Nunca place_order venue
- DEC-073

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_reports_f29.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Persistencia de scanner/optimize/montecarlo
- Órdenes venue / auto-flip LIVE
