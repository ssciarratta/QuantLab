# Binance Futures USD-M Testnet — Guía operativa

**Ámbito:** solo `testnet.binancefuture.com` (fapi) · **Producción:** bloqueada  
**Relacionado:** Spot → `docs/ops/BINANCE_TESTNET_SETUP.md`

## ¿Binance permite testear Spot y Futures?

Sí, en **venues distintos** con **API keys distintas**:

| Mercado | Host | Keys |
|---------|------|------|
| Spot Testnet | `testnet.binance.vision` | Portal Spot Testnet |
| Futures USD-M Testnet | `testnet.binancefuture.com` | Portal Futures Testnet |

Las keys de Hummingbot `binance_perpetual_testnet` son **Futures**, no Spot.

## Variables QuantLab

```bash
QUANTLAB_LIVE_USER=...
QUANTLAB_LIVE_PASSWORD=...
QUANTLAB_DEMO_USE_FUTURES_TESTNET=1
BINANCE_FUTURES_DEMO_API_KEY=...
BINANCE_FUTURES_DEMO_API_SECRET=...
```

**Importante:** no actives a la vez `QUANTLAB_DEMO_USE_TESTNET=1` y `QUANTLAB_DEMO_USE_FUTURES_TESTNET=1` (fail-closed).

## CLI

```bash
uv run quantlab-testnet status
uv run quantlab-testnet ping --market all
uv run quantlab-testnet balances --market futures
uv run quantlab-testnet diagnostic --market futures
uv run quantlab-testnet diagnostic --market all
```

## Transport

Post-unlock LIVE:

1. Default → `local_demo_sim`
2. Flag Spot + keys → `binance_spot_testnet`
3. Flag Futures + keys → `binance_futures_testnet`

Órdenes demo: `POST /api/live/demo/submit` (mismo path; el transport lo elige el router).

## Seguridad

- Rechaza `fapi.binance.com` / `dapi.binance.com` / Spot prod.
- `LIVE_BLOCKED=True` sin cambios.
- Secrets solo en `.env` local.
