# Arquitectura de información — Fase 2 (validada)

**Fecha:** 2026-08-11  
**Estado:** Implementada en `panel_registry.js`

## Decisión

Se adoptan **7 grupos por tarea** (no por módulo técnico), alineados con `USER_TASK_MAP.md`:

| Grupo | ID registry | Paneles principales |
|-------|-------------|---------------------|
| Inicio | `inicio` | home, chat, health |
| Investigar | `investigar` | scanner, universe, market, catalog |
| Probar | `probar` | simulator, backtest, montecarlo |
| Ejecutar en prueba | `ejecutar` | strategy_live_test |
| Monitorear | `monitorear` | blotter, journal, positions, risk |
| Resultados | `resultados` | sim_registry, reports, metrics |
| Sistema | `sistema` | settings, diagnostics, sessions… |

## Terminología

Nombres visibles en español según `UI_TERMINOLOGY.md`. El registry expone `label` (UI) y `subtitle` (técnico).

## Barra rápida (default)

`home · scanner · simulator · strategy_live_test · sim_registry · chat`

Configurable vía menú QL (localStorage `ql_menu_config_v6`).

## Flujo principal (Home)

Scanner → Simulador → Backtest → Monte Carlo → Ejecutar en prueba → Resultados

Implementado como `QLPanelRegistry.flowSteps` + rail clickeable en `home.js`.

## Paneles avanzados

Marcados `advanced: true` en registry (paper_session, binance_*, guided_lab, optimizer…). Siguen accesibles en menú; no en barra default.

## Espacios por tarea (cliente)

Presets en `QLPanelRegistry.layoutPresets` + `layout_presets.js` — **sin cambios de backend**.

## Métricas UX objetivo

- Boot: **1 ventana** (Inicio).
- Scanner → Corrida en vivo: **≤ 3 clics** (Home → Buscar → Ejecutar, o flujo rail).
- Menú: **7 secciones** vs 4 técnicas anteriores.
