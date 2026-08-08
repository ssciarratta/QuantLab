# FASE 102 — Binance Spot Testnet opt-in (HMAC)

**Versión:** 0.94.0 · **DEC-146** · **LIVE_BLOCKED:** True (sin unlock)

## Objetivo
Permitir órdenes demo remotas al **Spot Testnet** solo con doble gate:
1. Unlock LIVE (user/pass)
2. `QUANTLAB_DEMO_USE_TESTNET=1` + `BINANCE_DEMO_API_KEY` / `BINANCE_DEMO_API_SECRET`

Sin el flag, sigue el simulador local (F101). Nunca producción.

## DoD
- [x] Cliente firmado `BinanceTestnetClient` (stdlib)
- [x] Rechaza hosts de producción
- [x] Router elige transport según flag+keys
- [x] Tests mockeados (sin red real)
- [x] Sin `FASE_102_APPROVED.md`; secrets no en repo
- [x] `get_account` / `get_balances` / `auth_check` / `connectivity_check`
- [x] CLI `quantlab-testnet diagnostic` + scripts Windows `tools/windows/`
