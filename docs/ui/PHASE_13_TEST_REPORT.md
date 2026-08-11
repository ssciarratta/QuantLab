# Fase 13 — Reporte de tests UI

**Fecha:** 2026-08-11  
**Worktree:** `QuantLab-ui-redesign` · rama `feature/ui-radical-simplification`

## Smoke automatizado

Script: `scripts/smoke_ui_redesign.sh`

| Paso | Qué verifica | Resultado |
|------|----------------|-----------|
| 1 | Archivos estáticos (registry, ql_ui, home, monitor, tokens) | OK |
| 2 | `pytest tests/unit/execution/test_strategy_execution.py` | 14 passed |
| 3 | `GET /api/health` en `:8766` | OK |
| 4 | Static assets servidos | OK |
| 5 | `index.html` referencia panel_registry, home, monitor | OK |
| 6 | `POST /api/lab/binance/klines` | OK (bars JSON) |

## Verificación manual recomendada

1. `uv run quantlab-workbench` → abre solo **Inicio**
2. Menú QL → 7 grupos (Inicio, Investigar, Probar, …)
3. Abrir **Buscar oportunidades** → header ES + rail de flujo + botón siguiente
4. **Operación activa** → estado + órdenes + accesos rápidos
5. **Ejecutar en prueba** → duración + gráfico (requiere lightweight-charts CDN)

## Fase 12 — Sync backend

Backend `src/quantlab/` sincronizado desde repo principal (2026-08-11), preservando `workbench/static/` del redesign.

## Pendiente post-merge

- Push/PR cuando el usuario autorice
- Revisión visual paneles muy densos (scanner.js, simulator.js) — headers añadidos, contenido legacy intacto
