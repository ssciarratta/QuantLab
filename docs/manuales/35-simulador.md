# Manual — Simulador multi-venue

Panel para **comparar** markets (no reemplaza Guided Lab ni Monte Carlo).

## Cómo abrir

1. Menú **QL** → **Simulador** (o favorito / Ctrl+K → `simulador`)
2. **Mis simulaciones** (barra inferior · Sims) guarda memos y permite **Reabrir**

## Roles (no son lo mismo)

| Panel | Para qué |
|-------|----------|
| **Guided Lab** | Aprender / practicar en un flujo |
| **Simulador** | Comparar exchanges × monedas × leverage × fees |
| **Backtest** | 1 moneda × 1 estrategia × período (histórico o sintético debug) |
| **Optimizer** | Grid de params (lookback×qty) sobre la misma idea |
| **Monte Carlo** | Estrés N escenarios sobre esa selección (no predicción) |

## Flujo Comparar

1. Modo (spot/futuros) · leverage · período · TF · capital / fees.
2. Estrategia + **Correr y comparar** (o **Mejores estrategias** con 1 moneda).
3. Revisá la tabla HISTÓRICO · **Ver memorando**.
4. **Monte Carlo** (un solo botón): abre el panel ligado a la selección actual  
   (mercado + moneda + estrategia + params). No hay un segundo botón distinto.

### Botón Monte Carlo (único)

Antes había varios textos («con esta corrida», «con esta selección»): **hacían lo mismo**.  
Ahora hay **un** CTA «Monte Carlo» tras Comparar y otro atajo abajo; ambos pasan el mismo handoff `sim_context`.

## Mercados / monedas

- Sin monedas default: escribí para buscar · **+** · chips.
- Al tildar otro mercado se puede copiar la misma moneda.
- Venues: Binance / OKX / Bybit / Hyperliquid / A3.

## Fees y leverage

- Fees VIP0 por mercado (lab). Override manual → todos. **Fees mercado** restaura.
- Leverage 1–125.

## Stop / corridas concurrentes

Si hay otra corrida (Ranking, MC, Scanner…): diálogo **Esperar / Cortar / Cancelar**.  
**Stop** en el panel o en la barra inferior.

## API

- `GET /api/lab/sim/universe` · `fees` · `period`
- `POST /api/lab/sim/compare` · `rank-strategies` · `sizing`

## Invariantes

`LIVE_BLOCKED=True` · research-safe · REAL=PAPER
