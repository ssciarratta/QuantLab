# Alpha Scanner optimization — status

**Actualizado:** 2026-07-27  
**Fase actual:** FASE 3 — FeatureCalculator **COMPLETA**  
**Siguiente:** FASE 4 — Normalización robusta + CompositeScorer + PenaltyEngine

---

## FASE 0–2 — hecho

Ver historial abajo. Scoring `legacy_v1` **sin cambio**.

## FASE 3 — hecho

| Ítem | Estado |
|------|--------|
| `FeatureCalculator` modular | OK — `research/alpha/features.py` |
| Momentum / trend_quality / persistence | OK |
| Liquidity + spread (book o proxy HL/C) | OK |
| Depth / funding / OI | OK — `None` si no hay extras |
| Volume quality / volatility quality | OK |
| Legacy triple = AlphaScanner | OK — test parity |
| Ausencia → None (no 0 fingido) | OK |
| Scoring default cambiado | **No** |

### Archivos FASE 3

- Creados: `features.py`, `tests/unit/research/test_alpha_features_f3.py`

### Limitaciones F3

- Spread sin book = proxy rango OHLC (explícito).
- Features aún no alimentan el composite (FASE 4/5).

---

## Fases

| Fase | Título | Estado |
|------|--------|--------|
| 0 | Discovery & baseline | **DONE** |
| 1 | Modelos / contratos | **DONE** |
| 2 | Universo + calidad datos | **DONE** |
| 3 | Features modulares | **DONE** |
| 4 | Normalización / scoring | PENDING |
| 5–10 | Perfiles → auditoría | PENDING |

---

## Detalle FASE 2

| Ítem | Estado |
|------|--------|
| `DataQualityReport` + exclusiones tipadas | OK |
| Universe builder + API fetched/eligible/excluded | OK |
| UI Guided Lab exclusiones | OK |
