# Manual — Backtest

Una corrida: **1 moneda × 1 estrategia × período** (histórico MD público o sintético debug).

## Cómo abrir

1. Menú **QL** → **Backtest**
2. Ctrl+K → `backtest`
3. **Mis simulaciones** → Reabrir / Memo

## Invariantes

- `LIVE_BLOCKED=True` · REAL = PAPER
- Research-safe: no envía órdenes al venue

## Modos de datos

| Modo | Qué usa |
|------|---------|
| **Histórico** (default) | Venue + moneda + tipo + TF + período (mismas velas que Sim/MC) |
| **Sintético** | Velas inventadas del lab (`n_bars`) — solo debug |

El panel **informa** moneda, fuente, rango de fechas y estrategia en el contexto y en el memorando.

## Cómo usar

1. Datos = Histórico · mercado · moneda (ej. BTC) · período · TF · capital.
2. Elegí estrategia y params · **Correr** (hay **Stop**).
3. Leé el resumen (no solo el JSON) · **Ver memorando**.
4. Queda en **Mis simulaciones** → Reabrir.
5. Atajos: **→ Monte Carlo** · **→ Simulador**.

## Lectura

- Capital inicial/final, PnL, fees, fills, veredicto.
- Un buen lab **no** implica edge en vivo.

## API

`POST /api/lab/backtest` con `mode=historical` + `venue` + `underlying` + `period_days`  
o `mode=synthetic` + `n_bars`.

## Relacionado

Simulador · Monte Carlo · Optimizer · Reports
