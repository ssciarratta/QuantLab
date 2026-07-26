# FASE 50 — Review Package INTERNAL (Performance Baseline Workbench API)

**Fecha:** 2026-07-26  
**Versión código (impl F50):** 0.42.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Impl SHA:** `d91f239`  
**LIVE:** BLOQUEADO  
**Certificado externo:** **NO** (`FASE_50_APPROVED.md` no emitido)

---

## Resumen ejecutivo

Baseline de latencia loopback para endpoints clave del workbench API (health, mode, commands, about, lab/capabilities). Assert p95/max < 500ms. DEC-094 · bump 0.42.0.

**Opción elegida:** módulo `perf_baseline` + suite pytest + CLI; umbral generoso 500ms (peor p95 medido ≈ 7ms).

## Entregables

| ID | Entrega | Path |
|----|---------|------|
| A1 | Módulo perf_baseline | `src/quantlab/workbench/perf_baseline.py` |
| A2 | Suite F50 | `tests/unit/workbench/test_perf_baseline_f50.py` |
| A3 | CLI | `scripts/workbench_perf_baseline.py` |
| A4 | Spec | `docs/FASE_50_PERF_BASELINE.md` |
| A5 | Implementation report | `docs/audit/FASE_50_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-094 | `learning/decisiones.txt` |
| A7 | Version 0.42.0 | `pyproject.toml` |
| A8 | Smoke F50 | `scripts/internal_audit_smoke.py` |
| A9 | Bundle to-phase 50 | `scripts/build_internal_review_bundle.py` |

## Evidencia QA

```
uv run mypy --strict src/quantlab     → Success: 176 files
uv run ruff check                     → All checks passed
uv run pytest -q                      → 849 passed
uv run quantlab-health                → ok=true, live_blocked=true, version=0.42.0
uv run python scripts/internal_audit_smoke.py → 36/36 PASS
uv run python scripts/workbench_perf_baseline.py → PASS (p95≪500ms)
```

## Latencias (síntesis N=25)

| Path | p95 ms | max ms |
|------|--------|--------|
| `/api/health` | 7.26 | 19.80 |
| `/api/mode` | 0.37 | 0.51 |
| `/api/commands` | 0.66 | 0.70 |
| `/api/about` | 0.53 | 0.68 |
| `/api/lab/capabilities` | 0.42 | 0.56 |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_50_APPROVED.md`
- `phases_summary == "F19–F50 INTERNAL"`
