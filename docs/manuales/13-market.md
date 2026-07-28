# Manual — Market Data

Snapshot de market data del broker / fuente activa (read-oriented).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Inspeccionar precio/book o snapshot lab del símbolo actual.

## Cómo usar

1. Abrí **Market Data**.
2. Elegí símbolo / refrescá.
3. Usá la info para paper blotter o diagnóstico; no es terminal de trading LIVE.
