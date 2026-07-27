# Monte Carlo improvement — status

**Actualizado:** 2026-07-27  
**Branch:** `cursor/modo-real-workbench-aafd`

| Fase | Estado |
|------|--------|
| 0 Auditoría | **DONE** |
| 1 Modelos | **DONE** |
| 2 Persistencia + trazabilidad | **DONE** |
| 3 Compat schema v1 | **DONE** (normalize) |
| 4 Métricas backend | **DONE** (MonteCarloMetrics) |
| 5 Cabecera UI | **DONE** |
| 6 Panel qué simulamos | **DONE** |
| 7 Resultados legibles | **DONE** |
| 8 Histograma | **DONE** (canvas finales) |
| 9 Historial enriquecido | **DONE** (parcial: abrir) |
| 10 Navegación Scan/BT | **PARTIAL** (IDs + botones status) |
| 11 Tests | **DONE** subset F1+F2 |
| 12 Docs | **IN PROGRESS** |

## Notas

- Default lab sigue demo sintético BuyOnce + orphan warning si no hay scan/bt.
- UI: labels claros, RAW en `<details>`, histograma equities finales.
- API acepta `seed`, `scan_id`, `backtest_id`, `store_paths`.
