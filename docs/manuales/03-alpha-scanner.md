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
2. Elegí rama / perfil (Market making, Momentum, …).
3. (Opcional) ajustá **Kronos**: ON/OFF, Top 20/30, horizonte en velas, muestras.
4. Ejecutá **Escanear**.
5. Revisá columnas **Trad. / Kronos / Final**, ruptura y notas.
6. Continuá en Simulador / Backtest / Monte Carlo (mismo flujo de siempre).

## Kronos (dentro del Scanner)

- No es un panel aparte. Enriquecer ranking con forecast de horizonte.
- `legacy_v1` no altera el score (peso 0) salvo “Kronos en legacy”.
- Ausencia de Kronos → métricas `null` (nunca 0 fingido) + ranking tradicional.
- Detalle: `docs/scanner/kronos-inside-scanner.md`

## Perfiles (resumen)

- `legacy_v1`: 0.35 vol + 0.35 volume + 0.30 liquidity (min-max)
- Otros: ver `docs/scanner/alpha-scanner-guide.md`

## Walk-forward (pipeline Binance)

En Guided Lab / API pipeline: rank en tramo inicial, BT en tramo posterior (`rank_fraction` default 0.70).

## Límites

- No afirma rentabilidad.
- Funding/OI ausentes → `None` (nunca 0 fingido).
