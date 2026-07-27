# Monte Carlo improvement — status

**Actualizado:** 2026-07-27  
**Branch:** `cursor/modo-real-workbench-aafd`

| Fase | Estado |
|------|--------|
| 0 Auditoría | **DONE** |
| 1 Modelos | **DONE** |
| 2 Persistencia + trazabilidad | **DONE** |
| 3 Compat schema v1 | **DONE** (normalize) |
| 4 Métricas backend | **DONE** (+ probs ganancia/pérdida/≥inicial) |
| 5 Cabecera UI | **DONE** |
| 6 Panel qué simulamos | **DONE** |
| 7 Resultados legibles | **DONE** (cards + %) |
| 8 Histograma | **DONE** (canvas finales) |
| 9 Historial enriquecido | **DONE** (abrir / repetir / copiar id / eliminar) |
| 10 Navegación Scan/BT | **DONE** (QLShell.open + hint si no hay launcher) |
| 11 Tests | **DONE** (F1+F2+probs+DELETE) |
| 12 Docs | **DONE** |

## Notas

- Default lab sigue demo sintético BuyOnce + orphan warning si no hay scan/bt.
- UI: labels claros, RAW en `<details>`, histograma equities finales.
- API acepta `seed`, `scan_id`, `backtest_id`, `store_paths`.
- `DELETE /api/lab/montecarlo/history/{run_id}` cableado (sandbox sesión).
- Métricas: `prob_profit` (final>inicial), `prob_loss` (final<inicial), `prob_above_initial` (final≥inicial); normalize rellena en lectura v1 si hay `initial_equity`.
- Schema v1 de lectura no se fuerza a v2.
- Método MC único expuesto: `price_shock_rerun` (sin inventar bootstrap/etc.).
