# Manual — Monte Carlo

Estrés de equity bajo shocks de precio (dispersión, no predicción).

## Cómo abrir

1. Menú **QL** (barra inferior) → elegir el panel.
2. **Ctrl+K** (Command Palette) → escribir el nombre.
3. Presets: QL → Research / Trading Paper / Ops (abren conjuntos de paneles).

## Invariantes

- `LIVE_BLOCKED=True` por defecto: sin unlock no hay routing LIVE a venue.
- Modo **REAL** del producto = **PAPER** (fills simulados), no órdenes en exchange de producción.
- Este panel **no** garantiza rentabilidad ni es asesoramiento financiero.

## Para qué sirve

Medir dispersión de equities finales bajo ruido OHLC en un dataset (sintético o ligado a BT/scan).

## Parámetros clave

| UI | Código | Notas |
|----|--------|-------|
| Escenarios | `n_scenarios` | **2 … 1_000_000** (default tip: 1000) |
| Velas por escenario | `n_bars` | Velas 1m sintéticas (`WB:SYN`) usadas **por** escenario |
| Ruido bps | `noise_bps` | 10 bps = 0.10% |
| Seed | `seed` | Reproducibilidad |
| Confirmación | `confirm_large` | Requerida si N ≥ 100k |

**Importante:** el tope visual de trayectorias persistidas (~16) **no** limita N; solo cuántas paths se guardan.

## Modos

- `technical_lab`: dataset sintético demo.
- `normal`: exige `backtest_id` (ligazón a un BT real de sesión).

## Cómo usar

1. Abrí **Monte Carlo** (o deep-link desde Reports / Backtest / Guided Lab).
2. Revisá prefill (`backtest_id` / `scan_id`) si vino de otro panel.
3. Elegí N (presets: 100 / 1k / 10k / 100k / 1M).
4. Ejecutá; jobs grandes corren async (cancelable).
5. Leé media, desvío, histograma, IC de la **media** (no banda de un solo path).
6. Botones para abrir Reports / Guided Lab enfocando el id.

## Capital y fees

Mostrá capital inicial/final y fee por lado (lab tip VIP0 Spot 10 bps) para validar costos.

## Relacionado

- Guía: `docs/montecarlo/montecarlo-guide.md`
- Corrección: `docs/progress/montecarlo-correction-status.md`
