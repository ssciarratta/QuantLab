# Fase 5 Oficial — Feature Pipeline, Indicadores & Feature Store

**Numeración:** oficial alineada (`docs/ROADMAP_ALIGNED.md`)  
**No confundir** con la F5 local de ejecución (slippage/fees/artifacts).

| Módulo | Contenido | Estado |
|--------|-----------|--------|
| 1 | Feature Transformers + contratos | ✅ Certificado |
| 2 | Feature Pipeline composable + `run_universe` | ✅ Certificado |
| 3 | Feature Store + indicadores (SMA/EMA/RSI/ATR) | ✅ Certificado |

**Estado de fase:** 🟢 **APROBADO** — `docs/audit/FASE_05_OFFICIAL_APPROVED.md`  
**Deuda residual:** `docs/TECHNICAL_DEBT.md`

## Optimizaciones post-auditoría

- Ventanas deslizantes O(1): `VolumeSMA`, `SMAClose`, `ATR`
- Validación causal una sola vez en `FeaturePipeline.run`
- Serialización `str(Decimal)`; checksum SHA-256 sobre bytes de disco
- Caché en memoria en `FeatureStore.get`
- Tests: `tests/unit/features/test_perf_refactor.py`

## Módulo 1

- Certificado: `docs/audit/FASE_05_MODULO_01_APPROVED.md`
- `contracts.py`, `causal.py`, `transformers.py`
- `tests/unit/features/test_transformers_m1.py`

## Módulo 2

- `pipeline.py` — `FeaturePipeline`, `build_pipeline`, `FeatureFrame`
- `tests/unit/features/test_pipeline.py`

## Módulo 3

- `store.py` / `serialization.py` — Feature Store versionado + checksum
- `indicators.py` — SMA, EMA, RSI Wilder, ATR
- `tests/unit/features/test_store_m3.py`
- `tests/unit/features/test_indicators_m3.py`

## Invariantes

- `features` → `core` permitido; `core` ↛ `features`
- Anti-lookahead (prefijo estable)
- Decimal finito (sin NaN/Infinity)
- Resultados frozen
