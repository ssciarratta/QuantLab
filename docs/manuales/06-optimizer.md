# Manual — Optimizer

Búsqueda de parámetros de estrategia en el lab (grid/search acotado).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Explorar combinaciones de hiperparámetros y comparar métricas en sesión.

## Cómo usar

1. Abrí **Optimizer**.
2. Definí rango/grid y métrica objetivo.
3. Ejecutá y revisá ranking de candidatos.
4. Exportá / llevá el mejor set a Backtest o Experiments.

## Riesgos

- Overfitting: optimizar demasiado sobre el mismo sample.
- Preferí Validation Splits / walk-forward antes de confiar en un óptimo.
