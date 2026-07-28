# Manual — Salud / Modo

Estado del Workbench: versión, modo (tester/paper), LIVE_BLOCKED.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Verificar que el laboratorio está sano antes de operar paneles.

## Cómo usar

1. Abrí **Salud / Modo**.
2. Confirmá `LIVE_BLOCKED` y el modo (PAPER = REAL del producto).
3. Si el banner superior no coincide, refrescá este panel.
