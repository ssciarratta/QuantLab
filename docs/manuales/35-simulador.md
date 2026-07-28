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

## Roles (no son lo mismo)

| Panel | Para qué |
|-------|----------|
| **Guided Lab** | Aprender / practicar en un flujo (sobre todo Binance) |
| **Simulador** | Comparar exchanges × monedas × leverage × fees |
| **Backtest** | Motor 5A con velas **sintéticas** (debug técnico) |
| **Monte Carlo** | Estrés sobre un resultado ya corrido |

## Flujo en Comparar

1. **Estrategia primero** (selector + «¿Cómo opera?» + Correr).
2. **Mercados en fila** (uno al lado del otro): checkbox + menú moneda.
3. «¿Cómo opera?» abre una **ventana del escritorio** (mover, resize, minimizar, ×).

## Fees y leverage

- **Fees:** por defecto cada exchange usa su schedule VIP0 del lab (`GET /api/lab/sim/fees`).  
  Si editás maker/taker a mano → override para todos. Botón **Fees del mercado** restaura.
- **Leverage:** deslizador o número a mano (1–125).

## Elegir monedas (por exchange)

1. Activá el checkbox del exchange (Binance, OKX, Bybit, Hyperliquid).
2. En el menú desplegable elegí **Nombre completo (TICKER)** — ej. `Bitcoin (BTC)`.
3. **Agregar** — queda como chip; podés quitar con ×.
4. Cada par exchange×moneda se corre por separado (`pairs` en la API).

## Resumen tras correr

Tabla con: capital inicial, capital final, nº operaciones (fills), fees gastados, diferencia vs bench, liquidación.

Pasá el mouse sobre cada título (o celda) para ver una explicación corta.

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
