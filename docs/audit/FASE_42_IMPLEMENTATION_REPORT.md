# FASE 42 — Implementation Report (Ops Metrics Panel)

**Fecha:** 2026-07-26  
**Versión:** 0.34.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F41 Activity Log + Toasts  
**Alcance:** exponer ops_metrics en workbench (JSON + Prometheus + UI) — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Ops metrics core (existente) | `infra/ops_metrics.py` |
| A1 | `GET /api/ops/metrics` | `api.py` + `server.py` |
| A2 | `GET /api/ops/prometheus` | `api.py` + `server.py` |
| U1 | Panel Ops Metrics | `static/js/panes/ops_metrics.js` · `shell.js` · `index.html` · CSS |
| U2 | API client `getOpsMetrics` + command | `static/js/api.js` · `commands.py` |
| T1 | Tests F42 | `tests/unit/workbench/test_ops_metrics_f42.py` |
| T2 | Smoke F42 | `scripts/internal_audit_smoke.py` |
| D2 | Spec + DEC-086 + bump | `docs/FASE_42_OPS_METRICS.md` · `0.34.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Contadores in-process (sin persistencia histórica)
- Highlight `live_gate.blocked` cuando valor > 0
- DEC-086

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_ops_metrics_f42.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Certificado externo `FASE_42_APPROVED.md`
- Persistencia / scrape remoto de métricas
