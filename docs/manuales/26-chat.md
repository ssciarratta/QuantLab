# Manual — Chat IA

Asistente en safe-mode (guía / lectura; **no** envía órdenes).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Explicar paneles, interpretar métricas, buscar docs (`search_docs`).

## Cómo usar

1. Abrí **Chat IA**.
2. Preguntá en lenguaje natural.
3. Si el modelo sugiere una acción LIVE/orden: **ignorala** — el backend no debe ejecutar órdenes vía chat.

## Límites

- Requiere provider/API key según Settings / env.
- Memoria / instructor: ver fases F47 / F112.
- Nunca pegues secrets en el chat.
