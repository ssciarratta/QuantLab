# Fase 27 — Strategy Catalog (Workbench)

**Estado:** ✅ **APROBADO_INTERNO** (v0.19.0) — certificado externo `FASE_27_APPROVED.md` **NO** emitido  
**Base:** v0.18.0 · F26 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-071  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F27.md` · noche `INTERNAL_AUDIT_F19_F27_NIGHT.md`

## Objetivo
Ampliar el catálogo de estrategias usables desde workbench (paper session + lab backtest) con las research existentes `InventoryMMStrategy` y `AvellanedaStoikovStrategy`, más metadata para UI/API.

## DoD
- [x] Wire `InventoryMM` + `AvellanedaStoikov` en `paper_session` factory y `lab_services` backtest map
- [x] `GET /api/lab/strategies` + `strategy_catalog` en capabilities (id, nombre, defaults, tags)
- [x] UI: Sesión Paper + Backtest con selector completo + params básicos
- [x] Docs: `docs/FASE_27_STRATEGY_CATALOG.md` + IMPLEMENTATION_REPORT
- [x] Tests: cada `strategy_id` smoke step / backtest sin LIVE
- [x] DEC-071 · bump **0.19.0**

## Catálogo canónico

| id | tags | defaults clave |
|----|------|----------------|
| `dummy` | demo, momentum | quantity, price |
| `buy_once` | demo, momentum | quantity |
| `momentum` | momentum | quantity, lookback |
| `inventory_mm` | mm | quantity, half_spread, max_pos |
| `avellaneda_stoikov` | mm | quantity, gamma, sigma, kappa, horizon_events, max_pos |

Aliases: `simple_momentum`→`momentum`, `as`/`avellaneda`→`avellaneda_stoikov`, `inv_mm`→`inventory_mm`.

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/lab/strategies` | lista metadata completa |
| GET | `/api/lab/capabilities` | `strategies` (ids) + `strategy_catalog` |
| POST | `/api/paper/session/start` | `strategy_id` del catálogo + `params` |
| POST | `/api/lab/backtest` | idem |

## Notas técnicas
- Paper session inyecta `best_bid`/`best_ask`/`inventory` desde snapshot + PaperBook (necesario para MM).
- Lab backtest bar-based envuelve MM con `BarSyntheticBookAdapter` (mid ± half_spread desde close) — sin microestructura 5B.
- Sin flip LIVE · sin place_order venue.

## Fuera de alcance
LIVE · MicroBacktester 5B en lab UI · optimización multi-estrategia · WS exchange
