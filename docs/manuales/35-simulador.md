# Manual — Simulador multi-venue

Panel para **comparar** markets (no reemplaza Guided Lab ni Monte Carlo).

## Cómo abrir

1. Menú **QL** → **Simulador**
2. Ctrl+K → `simulador`

## Solapas

| Solapa | Uso |
|--------|-----|
| **Comparar** | Multi-venue + monedas por exchange + leverage/fees |
| **Estrategias** | Familias desplegables + popup “cómo opera” |

## Elegir monedas (por exchange)

1. Activá el checkbox del exchange (Binance, OKX, Bybit, Hyperliquid).
2. En el menú desplegable elegí **Nombre completo (TICKER)** — ej. `Bitcoin (BTC)`.
3. **Agregar** — queda como chip; podés quitar con ×.
4. Cada par exchange×moneda se corre por separado (`pairs` en la API).

## Controles

Spot/Futuros · leverage · período · capital · fees · liquidación/funding · gastos.

Atajos: Guided Lab · Monte Carlo · Paper Blotter.

## API

- `GET /api/lab/sim/universe` — monedas (nombre + ticker)
- `GET /api/lab/sim/fees|period`
- `POST /api/lab/sim/compare` — body con `pairs: [{venue, underlying}]`
- `POST /api/lab/sim/sizing`

## Invariantes

`LIVE_BLOCKED=True` · research-safe
