# FASE 101 — Binance demo routing post-unlock

**Versión:** 0.93.0 · **DEC-145** · **LIVE_BLOCKED:** True (sin unlock)

## Objetivo
Habilitar envío de órdenes **demo** Binance solo después del unlock user/pass.
Transport F101: simulador local (`local_demo_sim`). Sin pegar a producción.

## DoD
- [x] `LiveOrderRouter` construible tras unlock (scope binance_demo)
- [x] `POST /api/live/demo/submit` + `GET /api/live/demo/fills`
- [x] Sin unlock → 401 / ValidationError
- [x] Guided Lab paso 5
- [x] Activity `demo_submit` (sin password)
- [x] Sin `FASE_101_APPROVED.md`; secrets no en repo

## Fuera de alcance
- Testnet HMAC remoto (`BINANCE_DEMO_API_KEY/SECRET`)
- Producción Binance
- A3 live
