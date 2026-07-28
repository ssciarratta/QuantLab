# Manual — Features

Exploración / cómputo de features de research en el Workbench.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Inspeccionar transformaciones y series derivadas usadas por estrategias o scanners.

## Cómo usar

1. Abrí **Features**.
2. Elegí dataset / símbolo / ventana.
3. Generá o listá features y revisá salida.

## Límites

- Features lab no implican señal operable en vivo.
