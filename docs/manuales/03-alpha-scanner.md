# Manual — Alpha Scanner

Ranking de mercados según perfil de scoring (investigación).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Ordenar candidatos (sintéticos WB:A/B/C o universo Binance MD) por score compuesto.

## Cómo usar

1. Abrí **Alpha Scanner**.
2. Elegí perfil (`legacy_v1` default, momentum, mean_reversion, …).
3. Ejecutá **Escanear**.
4. Revisá ranking, exclusiones y `scan_id`.
5. Continuá en Guided Lab / Backtest / Monte Carlo.

## Perfiles (resumen)

- `legacy_v1`: 0.35 vol + 0.35 volume + 0.30 liquidity (min-max)
- Otros: ver `docs/scanner/alpha-scanner-guide.md`

## Walk-forward (pipeline Binance)

En Guided Lab / API pipeline: rank en tramo inicial, BT en tramo posterior (`rank_fraction` default 0.70).

## Límites

- No afirma rentabilidad.
- Funding/OI ausentes → `None` (nunca 0 fingido).
