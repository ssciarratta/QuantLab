# Manual — Hummingbot Export

Exportar configuración / artefactos compatibles con flujo Hummingbot (lab).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Generar un paquete de exportación para llevar parámetros del lab a un entorno HB externo.

## Cómo usar

1. Abrí **Hummingbot Export**.
2. Completá los campos requeridos.
3. Generá / descargá el artefacto.
4. Revisá el contenido antes de usarlo fuera de QuantLab.

## Límites

- QuantLab **no** rutea órdenes HB automáticamente.
- LIVE sigue bloqueado salvo unlock explícito en el producto.
