# Binance Spot Testnet — Guía operativa

**Versión:** 1.01.0+ · **Ámbito:** solo `testnet.binance.vision` · **Producción:** bloqueada

## Pipeline del producto

```text
Research → Backtest → Monte Carlo → Paper → Binance Spot Testnet → Live
   ✅          ✅           ✅         ✅            🟡              🔒
```

| Etapa | Estado actual | Notas |
|-------|---------------|-------|
| Research / Scanner | Habilitado | Sin órdenes venue |
| Backtest / Optimizer | Habilitado | Fees lab VIP0 |
| Monte Carlo | Habilitado | Export HB research-safe |
| Paper (REAL=PAPER) | Habilitado | Fills simulados |
| **Binance Spot Testnet** | **Opt-in F102** | Requiere unlock + flag + keys |
| Live producción | **BLOQUEADO** | `LIVE_BLOCKED=True` |

## Requisitos Testnet remoto

1. API keys en https://testnet.binance.vision (permiso **USER_DATA** + **TRADE** si luego autoriza órdenes).
2. Variables en `.env` local (nunca en git):

```bash
QUANTLAB_LIVE_USER=tu_usuario
QUANTLAB_LIVE_PASSWORD=tu_password
QUANTLAB_DEMO_USE_TESTNET=1
BINANCE_DEMO_API_KEY=...
BINANCE_DEMO_API_SECRET=...
```

3. Unlock LIVE en Workbench (`POST /api/live/unlock`) antes de routing demo remoto.

Sin el flag `QUANTLAB_DEMO_USE_TESTNET=1`, el transporte sigue siendo `local_demo_sim`.

## CLI `quantlab-testnet`

Instalado vía `pyproject.toml` (`quantlab-testnet`).

| Comando | Descripción |
|---------|-------------|
| `quantlab-testnet status` | Flags/keys (sin red) |
| `quantlab-testnet ping` | Ping + server time (público) |
| `quantlab-testnet balances` | Balances firmados (requiere keys) |
| `quantlab-testnet diagnostic` | Informe `TESTNET READY: YES/NO` |
| `quantlab-testnet hummingbot` | Estado HB externo |
| `quantlab-testnet hb-verify` | Scan configs HB vs producción |

Ejemplo:

```bash
uv run quantlab-testnet diagnostic
```

## Seguridad

- `BinanceTestnetClient` rechaza `api.binance.com` y `api.binance.us`.
- `base_url` debe contener `testnet` o `binance.vision`.
- Secrets nunca se loguean ni van al repositorio.
- El diagnóstico **no crea órdenes**.

## API cliente (F102 extendido)

- `connectivity_check()` — ping + time
- `auth_check()` — `GET /api/v3/account` sin órdenes
- `get_account()` / `get_balances()` — balances testnet
- `recvWindow` configurable (default 5000 ms)
- Reintento automático en error `-1021` (skew de reloj)

## Windows

Ver `tools/windows/README.md` para scripts `.bat` numerados.

## Relación con Hummingbot

QuantLab **no** ejecuta Hummingbot. Exporta JSON research-safe; testnet spot nativo es F102.
Hummingbot spot usa `binance_paper_trade` (paper) — no existe connector `binance_testnet` spot en HB.

Ver `docs/ops/HUMMINGBOT_TESTNET.md`.
