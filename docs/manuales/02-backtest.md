# Manual — Backtest

Correr un backtest de laboratorio sobre dataset sintético o referenciado.

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Evaluar una estrategia en histórico lab (métricas, equity, fills, fees).

## Cómo usar

1. Abrí **Backtest**.
2. Completá parámetros (estrategia, barras, capital inicial, fee por lado si aplica).
3. Ejecutá y esperá el resultado.
4. Revisá Metrics / Reports para el historial de la sesión.
5. Botón **→ Monte Carlo** (cuando hay `report_id`) para estrés.

## Lectura de resultados

- Capital inicial / final y fees totales ayudan a validar el modelo de costos.
- Un backtest bueno en lab **no** implica edge en vivo.

## Relacionado

- Guided Lab (flujo guiado)
- Reports / Metrics
- Monte Carlo (mode `normal` exige `backtest_id`)
