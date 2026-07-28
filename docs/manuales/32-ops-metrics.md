# Manual — Ops Metrics

Métricas operativas del proceso Workbench.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Observabilidad liviana (latencias, contadores) para ops.

## Cómo usar

1. Abrí **Ops Metrics**.
2. Refrescá y anotá anomalías.
3. Complementá con Diagnostics si necesitás bundle.
