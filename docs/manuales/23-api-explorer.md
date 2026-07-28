# Manual — API Explorer

Explorador OpenAPI read-only del Workbench.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Descubrir endpoints documentados sin Postman.

## Cómo usar

1. Abrí **API Explorer**.
2. Navegá paths / schemas.
3. Las llamadas destructivas / LIVE siguen fail-closed en el servidor.
