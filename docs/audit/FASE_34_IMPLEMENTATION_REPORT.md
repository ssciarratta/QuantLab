# FASE 34 — Implementation Report (Monte Carlo History + HB Export Wizard)

**Fecha:** 2026-07-26  
**Versión:** 0.26.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F33 Optimizer UI · F21 Lab · F11 Monte Carlo · F16 Hummingbot export  
**Alcance:** historial MC + wizard export HB — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| S1 | Persist MC runs | `workbench/montecarlo_runs.py` |
| S2 | List HB exports | `workbench/hb_exports.py` |
| S3 | Session `montecarlo_dir` | `workbench/session.py` |
| L1 | `run_lab_montecarlo` + persist + CI | `workbench/lab_services.py` |
| L2 | `run_lab_export_hb` wizard steps | `workbench/lab_services.py` |
| A1 | `GET /api/lab/montecarlo/history` (+ `/{id}`) | `api.py` + `server.py` |
| A2 | `GET /api/lab/exports` (+ `/{id}`) | `api.py` + `server.py` |
| A3 | POST montecarlo / export-hb enriquecidos | `api.py` + `server.py` |
| U1 | Panel Monte Carlo enriquecido | `static/js/panes/montecarlo.js` |
| U2 | Panel Export HB wizard | `static/js/panes/export_hb.js` |
| T1 | Tests F34 | `tests/unit/workbench/test_mc_export_f34.py` |
| D1 | Spec + DEC-078 + bump | `docs/FASE_34_MC_EXPORT.md` · `0.26.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Persist solo sandbox sesión
- Path externo rechazado
- Export siempre `live_routing: false`
- Nunca place_order venue
- DEC-078

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_mc_export_f34.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Order routing Hummingbot real
- Órdenes venue / auto-flip LIVE
- Certificado externo `FASE_34_APPROVED.md`
