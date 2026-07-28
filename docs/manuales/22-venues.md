# Manual — Venues

Registry read-only de brokers / venues conocidos.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Ver qué plugins/venues están registrados y su estado (paper, demo, MD).

## Cómo usar

1. Abrí **Venues**.
2. Refrescá la tabla.
3. No edita credenciales secretas aquí.
