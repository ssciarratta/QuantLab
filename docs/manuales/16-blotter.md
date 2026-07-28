# Manual — Paper Blotter

Enviar órdenes **paper** manuales (fills simulados).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Probar ticket de orden sin venue real.

## Cómo usar

1. Abrí **Paper Blotter**.
2. Completá símbolo, lado, qty, tipo.
3. Enviá → el fill aparece en **Journal**.
4. Revisá **Posiciones** / **Riesgo**.

## Límites

- No es ejecución en Binance prod.
- Con LIVE unlock, otros paneles pueden usar demo; el blotter paper sigue siendo simulación local salvo flujos demo documentados.
