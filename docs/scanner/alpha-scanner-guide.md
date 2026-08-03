# Alpha Scanner — documentación final (FASE 10)

**Fecha:** 2026-07-27 · Kronos: 2026-08-03  
**Versión tip:** 1.01.0  
**Estado código:** FASE 0–10 + walk-forward pipeline + Kronos-inside-Scanner · cierre formal de auditoría **pendiente**  
**Manual de panel:** [`../manuales/03-alpha-scanner.md`](../manuales/03-alpha-scanner.md) · índice [`../manuales/00-INDICE.md`](../manuales/00-INDICE.md)  
**Kronos:** [`kronos-inside-scanner.md`](kronos-inside-scanner.md)

---

## Qué es

Herramienta de **investigación** para rankear mercados según un perfil.
**No** afirma rentabilidad. `LIVE_BLOCKED` se mantiene.

Con Kronos (extra opcional) el ranking también considera el horizonte futuro
estimado (solo tramo de ranking; anti-leakage). Flujo externo intacto:
Scanner → Sim/BT → MC.

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
Cada ítem incluye `name`, `description`, `label_es` (selector Guided Lab).

## Walk-forward (pipeline Binance)

Por defecto el pipeline `POST /api/lab/binance/pipeline` usa **walk-forward**:

| Campo | Default | Rol |
|-------|---------|-----|
| `walk_forward` | `true` | Ranking en tramo inicial; backtest en tramo posterior |
| `rank_fraction` | `0.70` | Fracción de velas para ranking (resto → BT) |

- **Sin overlap** temporal entre rank y BT.
- Requiere `kline_limit >= 16` cuando `walk_forward=true`.
- Opt-out: `walk_forward=false` → misma ventana rank+BT (**selección in-sample**; sesgo).
- Implementación: `research/alpha/walk_forward.py` · `lab_services.run_binance_lab_pipeline`.

Guided Lab (venue Binance): checkbox **walk-forward (rank ≠ BT)** (ON por defecto), input **rank_fraction**, leyenda en el panel. El resumen del pipeline muestra `walk_forward` y `rank_fraction`.

**Importante:** walk-forward reduce sesgo de selección in-sample; **no** garantiza rentabilidad out-of-sample.

## Exclusiones

Motivos tipados (`fetch_failed`, `insufficient_history`, …).  
Ausencia de funding/OI/depth → `None` (nunca 0 fingido).

## Limitaciones

1. Con `walk_forward=false`, pipeline rank+backtest comparte ventana (selección in-sample).
2. Binance público sin `as_of` → no reproducible a fecha histórica exacta.
3. HL/Bybit/OKX: capabilities declaradas; fetch MD **no** implementado.
4. Spread sin order book = proxy HL/C.
5. Score ≠ PnL.

## Archivos clave

- `research/alpha/` — models, quality, universe, features, scoring, profiles, venues, persist, observe, walk_forward
- `workbench/lab_services.run_binance_lab_scanner` — default legacy
- `workbench/lab_services.run_binance_lab_pipeline` — walk-forward por defecto
- Guided Lab — selector perfil (`label_es`) + modo avanzado + opt-out walk-forward

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
| Post | Walk-forward pipeline + UI opt-out / rank_fraction |
