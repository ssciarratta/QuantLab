# Manual — Optimizer

Grid **lookback × quantity** (momentum) sobre velas históricas o sintéticas.

## Cómo abrir

1. Menú **QL** → **Optimizer**
2. Ctrl+K → `optimizer`
3. **Mis simulaciones** → Reabrir / Memo

## Invariantes

- `LIVE_BLOCKED=True` · REAL = PAPER
- Máx. 12 trials por corrida (anti-abuso)

## Modos de datos

| Modo | Qué usa |
|------|---------|
| **Histórico** (default) | Venue + moneda + TF + período (MD público) |
| **Sintético** | `n_bars` 8–60 (debug) |

Contexto visible: moneda · mercado · velas · rango. Memo + registro como Sim/Backtest.

## Cómo usar

1. Histórico · moneda · período · capital.
2. lookbacks (ej. `2,3`) · qty (ej. `1`) · **Optimizar** (**Stop** disponible).
3. Mejor trial + tabla + Pareto sharpe/MDD.
4. **Ver memorando** · Mis simulaciones → Reabrir.
5. Atajos: **→ Backtest** · **→ Simulador**.

## Riesgos

- Overfitting sobre el mismo sample.
- Preferí Validation / walk-forward antes de confiar en un óptimo.

## API

`POST /api/lab/optimize` con `mode=historical` + venue/underlying/period_days  
o `mode=synthetic` + `n_bars`.
