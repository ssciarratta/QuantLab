# Monte Carlo correction — status

**Actualizado:** 2026-07-27  
**Fase actual:** FASE 0–12 **código listo** (cierre formal auditoría externo no aplica)

| Fase | Estado |
|------|--------|
| 0 Auditoría | **DONE** — `docs/montecarlo/montecarlo-correction-audit.md` |
| 1 n_scenarios 1e6 | **DONE** — `limits.py` + lab/API/UI |
| 2 trayectorias ≠ N | **DONE** — max_persisted_trajectories independiente |
| 3 batching / stats | **DONE** — Welford + histograma + reservoir |
| 4 progreso / cancel | **DONE** — jobs async + CancellationToken |
| 5 n_bars semántica | **DONE** — “Velas utilizadas por escenario” + bars_meta |
| 6 DatasetReference | **DONE** — `montecarlo/dataset.py` |
| 7 Abrir dataset | **DONE** — detalle inline UI |
| 8 Abrir scan/BT | **DONE** — enable/disable + tooltips |
| 9 anti-huérfanos | **DONE** — mode normal vs technical_lab |
| 10 resultados grandes | **DONE** — storage_mode summary_and_sample |
| 11 schema compat | **DONE** — lectura v1 intacta; payload enriquecido v2 |
| 12 tests / docs | **DONE** — `test_correction_limits.py` · **45 passed** MC suite |

## Verificación ejecutada

```
pytest tests/unit/montecarlo tests/unit/workbench/test_sim_capital_fees.py \
  tests/unit/workbench/test_mc_export_f34.py -q
→ 45 passed
ruff + mypy (paquete montecarlo + jobs) → OK
```

## Notas

- Default UI: 1000 escenarios · 60 velas/escenario · moneda LAB (sintético).
- N≥100k requiere `confirm_large=true`.
- N≥5000 → job async por defecto.
- Máx 16 aplica **solo** a trayectorias guardadas, no a N.
