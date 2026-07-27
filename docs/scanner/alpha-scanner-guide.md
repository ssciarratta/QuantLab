# Alpha Scanner — documentación final (FASE 10)

**Fecha:** 2026-07-27  
**Versión tip:** 1.01.0  
**Estado código:** FASE 0–9 implementadas · cierre formal de auditoría **pendiente**

---

## Qué es

Herramienta de **investigación** para rankear mercados según un perfil.
**No** afirma rentabilidad. `LIVE_BLOCKED` se mantiene.

## Fórmula default (`legacy_v1`)

```
composite = 0.35·n(vol) + 0.35·n(volume) + 0.30·n(liquidity)
```

`n` = min-max cross-sectional. Núcleo: `AlphaScanner` en `research/alpha/__init__.py`.

## Perfiles

| Perfil | Idea |
|--------|------|
| `legacy_v1` | Fórmula F4/F111 (default lab) |
| `momentum` | momentum + trend + vol + volume |
| `mean_reversion` | anti-momentum + liquidez |
| `market_making` | liquidez + spread estrecho |
| `avellaneda_stoikov` | spread/vol/liquidez |
| `funding` | funding/OI (renormaliza si faltan) |
| `balanced` | mezcla + norm robusta |

Catálogo: `GET /api/lab/alpha/profiles`

## Exclusiones

Motivos tipados (`fetch_failed`, `insufficient_history`, …).  
Ausencia de funding/OI/depth → `None` (nunca 0 fingido).

## Walk-forward (pipeline Binance)

`POST /api/lab/binance/pipeline` con `walk_forward=True` (**default**):

- ~70% barras → ranking / score
- ~30% barras → backtest top-N
- Sin overlap entre ventanas (`split_bars_walk_forward`)

Con `walk_forward=False` rank y BT pueden compartir historia (selección in-sample; no recomendado).

## Limitaciones

1. Con `walk_forward=False`, rank+backtest pueden compartir ventana (selección in-sample).
2. Binance público sin `as_of` → no reproducible a fecha histórica exacta.
3. HL/Bybit/OKX: capabilities declaradas; fetch MD **no** implementado.
4. Spread sin order book = proxy HL/C.
5. Score ≠ PnL.

## Archivos clave

- `research/alpha/` — models, quality, universe, features, scoring, profiles, venues, persist, observe
- `workbench/lab_services.run_binance_lab_scanner` — default legacy
- Guided Lab — selector perfil + modo avanzado

## Tests

```bash
.venv/Scripts/python.exe -m pytest tests/unit/research/test_alpha_*.py tests/unit/workbench/test_binance_lab_f111.py -q
```

## Changelog corto

| Fase | Entrega |
|------|---------|
| 0–1 | Auditoría + contratos |
| 2 | Universo / calidad |
| 3 | FeatureCalculator |
| 4 | CompositeScorer |
| 5 | Perfiles |
| 6 | Multi-venue caps |
| 7 | Persistencia / hashes |
| 8 | UX Guided Lab |
| 9 | Cache / progreso / cancel |
| 10 | Esta guía |
| Post | Walk-forward pipeline (rank ≠ BT) |
