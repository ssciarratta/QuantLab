# Manual — Reconciliación

Estado de reconciliación paper (journal vs book).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Detectar inconsistencias post-rebuild o tras muchos fills.

## Cómo usar

1. Abrí **Reconciliación**.
2. Refrescá status.
3. Si hay mismatch, no asumas venue real: corregí paper / rehydrate según docs F88–F91.
