# Manual — Sesión Paper

Runner de estrategia automática en paper (lab).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Dejar una estrategia corriendo contra fills simulados en la sesión.

## Cómo usar

1. Abrí **Sesión Paper**.
2. Elegí estrategia / parámetros.
3. Start / stop según controles del panel.
4. Monitoreá Journal, Posiciones y Riesgo.

## Límites

- No arranca routing LIVE por sí solo.
