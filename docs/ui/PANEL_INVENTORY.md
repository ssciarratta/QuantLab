# Inventario de paneles — QuantLab Workbench

**Total:** 39 paneles MDI + About (modal) + `sim_registry` + ventanas `sim_memo_*`  
**Registro canónico:** `shell.js` → `openers`  
**Menú:** `ql_menu.js` (4 secciones)

Leyenda categoría: **INV** Investigar · **PRB** Probar · **EJE** Ejecutar · **MON** Monitorear · **RES** Resultados · **SYS** Sistema

| ID | Label actual | Archivo | Cat. | Acción principal | Problema UX | Duplicados |
|----|--------------|---------|------|------------------|-------------|------------|
| chat | Chat IA | panes/chat.js | INV | Preguntar / abrir paneles | Solapa con Docs | docs |
| scanner | Alpha Scanner | panes/scanner.js | INV | Escanear ranking | Toolbar densa, Kronos/TF | simulator, guided_lab |
| simulator | Simulador | panes/simulator.js | PRB | Comparar mercados | ~3084 LOC, abrumador | backtest, optimize |
| montecarlo | Monte Carlo | panes/montecarlo.js | PRB | Simular escenarios | scan_id visible | backtest, reports |
| strategy_live_test | Corrida en vivo | panes/strategy_live_test.js | EJE/MON | INICIAR corrida | Muchos tabs/tooltips | paper_session |
| sim_registry | Mis simulaciones | sim_registry.js | RES | Reabrir run | localStorage denso | reports, metrics |
| strategies | Estrategias | panes/strategies.js | INV | Ver catálogo | IDs técnicos | live test, simulator |
| guided_lab | Guided Lab | panes/guided_lab.js | INV/PRB/EJE | Wizard venue | Monolito multi-flujo | casi todo el lab |
| backtest | Backtest | panes/backtest.js | PRB | Correr histórico | Params dinámicos | simulator |
| binance_spot | Spot Testnet | panes/binance_testnet.js | EJE | Unlock / demo order | Copy técnico | futures, live test |
| binance_futures | Futures Testnet | panes/binance_testnet.js | EJE | Idem spot | Idem | binance_spot |
| health | Salud / Modo | panes/health.js | MON/SYS | Cambiar modo | REAL=paper confuso | diagnostics, about |
| market | Market Data | panes/market.js | INV/MON | Conectar MD | GGAL vs crypto | venues |
| universe | Universe | panes/universe.js | INV | Watchlist | "Add" EN | scanner |
| catalog | Data Catalog | panes/catalog.js | INV | Listar datasets | Solo lectura plana | features |
| blotter | Paper Blotter | panes/blotter.js | EJE/MON | Submit paper | EN, PnL dup | journal, positions |
| journal | Journal | panes/journal.js | RES/MON | Ver fills | F65 en copy | blotter |
| paper_session | Sesión Paper | panes/paper_session.js | EJE/MON | Start/Step/Stop | Params crudos | strategy_live_test |
| positions | Posiciones | panes/positions.js | MON | Ver PnL MTM | Rutas API en UI | blotter |
| risk | Riesgo | panes/risk.js | MON | Kill switch | slippage_bps crudo | paper_session |
| reconciliation | Reconciliación | panes/reconciliation.js | MON | Book vs journal | "rehydrate" | diagnostics |
| metrics | Metrics / Último | panes/metrics.js | RES | Ver JSON | Sin UI amigable | reports |
| reports | Reports | panes/reports.js | RES | Preview informe | Mejor que metrics | sim_registry |
| experiments | Experiments | panes/experiments.js | RES | Listar JSON | Mínimo | export_hb |
| optimize | Optimizer | panes/optimize.js | PRB | Grid params | momentum hardcoded | backtest |
| features | Features | panes/features.js | INV | Pipeline features | Muy dev | catalog |
| export_hb | Hummingbot Export | panes/export_hb.js | RES | Export HB | live_routing banner | experiments |
| validation | Validation Splits | panes/validation.js | PRB | Walk-forward | n_bars EN | backtest |
| venues | Venues / Mercados | panes/venues.js | INV/SYS | Listar venues | Label inconsistente | market |
| api_explorer | API Explorer | panes/api_explorer.js | SYS | Ver endpoints | Dev tool | docs |
| diagnostics | Diagnostics | panes/diagnostics.js | SYS | Bundle JSON/ZIP | EN fallback | health |
| sessions | Sessions | panes/sessions.js | SYS | Cambiar sesión | EN | settings |
| activity | Activity | panes/activity.js | SYS/MON | Log actividad | Crudo | access_log |
| access_log | Access Log | panes/access_log.js | SYS | HTTP log 5s | LIVE en meta | activity |
| backups | Backups | panes/backups.js | SYS | Backup now | Opaco | settings |
| ops_metrics | Ops Metrics | panes/ops_metrics.js | SYS/MON | Counters | Sin gráficos | health |
| settings | Settings | panes/settings.js | SYS | Preferencias | Bloque único denso | sessions |
| docs | Help / Docs | panes/docs.js | SYS/INV | Buscar docs | OK | chat |
| about | Acerca de | about.js (modal) | SYS | Ver versión | Técnico | health |

## Ventanas no registradas en menú

| ID | Origen | Notas |
|----|--------|-------|
| sim_memo_* | sim_registry, scanner, etc. | Memorandos dinámicos |
| onboarding | onboarding.js | Primer arranque |

## Boot automático (shell.js)

- `health`, `market`, `blotter` — **propuesta:** reemplazar por **Inicio** solo.

## Barra rápida default (8 ítems)

Propuesta reducir a 5: Chat · Buscar · Comparar · Ejecutar en prueba · Mis simulaciones.

---

Plantilla por panel (fase rollout):

```text
Nombre actual:
Objetivo real:
Usuario objetivo:
Acciones principales:
Acciones secundarias → AdvancedSettings
Información imprescindible:
Información avanzada:
Dependencias API:
Propuesta rediseño:
```

Detalle extendido por panel: ver subagente auditoría 2026-08-11 en historial del epic UI.
