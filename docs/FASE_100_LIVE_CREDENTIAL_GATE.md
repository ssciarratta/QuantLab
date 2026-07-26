# FASE 100 — LIVE credential gate + Binance public MD

**Versión:** 0.92.0 · **DEC-144** · **LIVE_BLOCKED:** True (sin unlock)

## Objetivo
Desarrollar el camino LIVE con corte humano (user/pass) y scan Binance MD real read-only.

## DoD
- [x] Unlock/lock/status API
- [x] Sin unlock → assert_live_routing_blocked falla
- [x] Con unlock válido → ModeGuard LIVE permite boot; router aún stub
- [x] Binance public scan
- [x] Guided Lab UI unlock + scan Binance
- [x] Sin FASE_100_APPROVED.md; secrets no en repo
