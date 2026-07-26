# FASE 34 — Review Package INTERNAL (Monte Carlo History + HB Export)

**Fecha:** 2026-07-26  
**Versión código (impl F34):** 0.26.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** POST `/api/lab/montecarlo` persiste `summary.json` bajo `montecarlo/<run_id>/`; GET `/api/lab/montecarlo/history` lista/latest; panel UI con CI. Export HB wizard lista experiments, corre validate→build→export path-safe (snapshot + alias latest); GET `/api/lab/exports` lista; banner `live_routing:false` (DEC-078).

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Persist MC | `workbench/montecarlo_runs.py` |
| A2 | List exports | `workbench/hb_exports.py` |
| A3 | Session montecarlo_dir | `workbench/session.py` |
| A4 | Lab runners | `workbench/lab_services.py` |
| A5 | API + server | `api.py` · `server.py` |
| A6 | Spec | `docs/FASE_34_MC_EXPORT.md` |
| A7 | Implementation report | `docs/audit/FASE_34_IMPLEMENTATION_REPORT.md` |
| A8 | DEC-078 | `learning/decisiones.txt` |
| A9 | Panel MC | `static/js/panes/montecarlo.js` |
| A10 | Panel Export wizard | `static/js/panes/export_hb.js` |
| A11 | Suite F34 | `tests/unit/workbench/test_mc_export_f34.py` |
| A12 | Version 0.26.0 | `pyproject.toml` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.26.0
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

LIVE flip · auth WAN · HB order routing real · certificado externo `FASE_34_APPROVED.md`
