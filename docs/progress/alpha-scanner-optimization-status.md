# Alpha Scanner optimization — status

**Actualizado:** 2026-07-27  
**Fase actual:** FASE 5 — Perfiles **COMPLETA**  
**Siguiente:** FASE 6 — Multi-venue (Binance + capabilities Hyperliquid/Bybit/OKX)

---

## Hecho (0–5)

| Fase | Resumen |
|------|---------|
| 0 | Auditoría + baseline sintético |
| 1 | Contratos tipados `legacy_v1` |
| 2 | Universo + exclusiones tipadas |
| 3 | `FeatureCalculator` (ausencia→None) |
| 4 | `CompositeScorer` + norm + penalties |
| 5 | Perfiles nombrados + `score_with_profile` |

**Default lab:** sigue `AlphaScanner` / `legacy_v1` (parity en tests).

### Perfiles F5

`legacy_v1` · `momentum` · `mean_reversion` · `market_making` · `avellaneda_stoikov` · `funding` · `balanced`

Archivos: `research/alpha/profiles.py`, `tests/unit/research/test_alpha_profiles_f5.py`

---

## Pendiente

| Fase | Título |
|------|--------|
| 6 | Multi-venue |
| 7 | Persistencia / reproducibilidad |
| 8 | Workbench / Guided Lab UX |
| 9 | Rendimiento / observabilidad |
| 10 | Docs / auditoría final |
