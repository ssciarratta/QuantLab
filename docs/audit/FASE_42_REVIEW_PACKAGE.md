# FASE 42 — Review Package INTERNAL (Ops Metrics Panel)

**Fecha:** 2026-07-26  
**Versión código (impl F42):** 0.34.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** reutilizar `quantlab.infra.ops_metrics` (contadores in-process); `GET /api/ops/metrics` JSON + `GET /api/ops/prometheus` text/plain; UI panel tabla con highlight `live_gate.blocked`. DEC-086.

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Ops metrics core | `infra/ops_metrics.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Panel UI | `panes/ops_metrics.js` · `shell.js` · `index.html` · CSS |
| A4 | Spec | `docs/FASE_42_OPS_METRICS.md` |
| A5 | Implementation report | `docs/audit/FASE_42_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-086 | `learning/decisiones.txt` |
| A7 | Suite F42 | `tests/unit/workbench/test_ops_metrics_f42.py` |
| A8 | Version 0.34.0 | `pyproject.toml` |
| A9 | Impl SHA | `34bfac5` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.34.0
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

LIVE flip · auth WAN · browser E2E · certificado externo `FASE_42_APPROVED.md` · persistencia histórica / scrape remoto
