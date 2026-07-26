# FASE 41 — Review Package INTERNAL (Activity Log + Toasts)

**Fecha:** 2026-07-26  
**Versión código (impl F41):** 0.33.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** módulo `workbench/activity.py` con JSONL append-only por sesión; hooks mínimos en handlers connect/submit/backtest/optimize/export; `GET /api/activity`; UI toasts + panel Activity. DEC-085.

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Activity core | `workbench/activity.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Hooks eventos | `api.py` (_record_activity) |
| A4 | Toasts + panel | `toasts.js` · `panes/activity.js` · `shell.js` · `index.html` |
| A5 | Spec | `docs/FASE_41_ACTIVITY.md` |
| A6 | Implementation report | `docs/audit/FASE_41_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-085 | `learning/decisiones.txt` |
| A8 | Suite F41 | `tests/unit/workbench/test_activity_f41.py` |
| A9 | Version 0.33.0 | `pyproject.toml` |
| A10 | Impl SHA | `f1db945` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.33.0
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

LIVE flip · auth WAN · browser E2E · certificado externo `FASE_41_APPROVED.md` · truncate/rotate log
