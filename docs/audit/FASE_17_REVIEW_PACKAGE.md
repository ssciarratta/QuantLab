# Review Package — FASE 17 + residuos F10/F12/F14

**Fecha:** 2026-07-25  
**Versión código:** 0.9.0  
**Tipo:** Review Package de trabajo (Meta-Auditor)  
**NO es** `FASE_17_APPROVED.md` — requiere APROBADO explícito.

---

## Lista A — Entregables a auditar

| ID | Entregable | Path |
|----|------------|------|
| A1 | ParallelBatchRunner / monitor / backup | `src/quantlab/scale/` |
| A2 | ParallelBacktester (ProcessPool) | `src/quantlab/backtester/parallel_runner.py` |
| A3 | Parquet + DuckDB catalog | `parquet_store.py`, `duckdb_backend.py` |
| A4 | `adjust_pvalues` / `filter_significant` | `validation/multiple_testing.py` |
| A5 | `compute_pareto_frontier` | `optimizer/pareto.py` |
| A6 | Avellaneda–Stoikov + `quote_prices` | `research/strategies/avellaneda_stoikov.py` |
| A7 | LIVE gate `LIVE_BLOCKED=True` | `execution/live_gate.py` |
| A8 | Suite control residuos | `tests/unit/test_phase_residual_completion.py` |
| A9 | Suite F17 | `tests/unit/scale/test_fase17_and_residuals.py` |

## Lista B — Evidencia QA

```
uv run mypy --strict src/quantlab   → Success
uv run ruff check src/quantlab      → All checks passed
uv run pytest tests/unit/test_phase_residual_completion.py → 6 passed
uv run pytest -q                    → 191 passed
```

## Invariantes

- LIVE order routing: **BLOQUEADO** (`LIVE_BLOCKED = True`)
- Separación dominio/ejecución (DEC-014/036/040)
- Sin certificado formal hasta APROBADO Meta-Auditor

## Pedido al Meta-Auditor

1. Revisar Lista A+B.  
2. Emitir **APROBADO** / observaciones.  
3. Solo con APROBADO → generar `docs/audit/FASE_17_APPROVED.md`.
