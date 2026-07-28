# Manual — Validation Splits

Particiones train/validation/test (o walk-forward splits) para experimentos de research.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Definir y revisar cortes temporales de datos para evitar evaluar siempre in-sample.

## Cómo usar

1. Abrí **Validation Splits**.
2. Refrescá / generá splits según el flujo del panel.
3. Usá los ids/rangos al configurar backtests o experimentos.

## Límites

- Es herramienta de laboratorio; no sustituye validación out-of-sample real de producción.
