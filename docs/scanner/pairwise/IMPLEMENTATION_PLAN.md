# Fase 2 — Plan de implementación verificable

**Fecha:** 2026-08-12  
**Prerequisitos:** `AUDIT.md`, `DESIGN.md`  
**Git restore point:** `restore/pre-pairwise-integration-20260812`

Cada fase entrega código + tests + criterio objetivo. **No avanzar** sin verificación verde.

---

## Resumen de fases

| Fase | Entregable | Depende de |
|------|------------|------------|
| **IP-0** | Docs AUDIT/DESIGN/PLAN | — |
| **IP-1** | Contrato `AlphaSignal` + registry | IP-0 |
| **IP-2** | Adapter legacy + normalización percentil | IP-1 |
| **IP-3** | Universo pares + alineación temporal | IP-1 |
| **IP-4** | Detector `lagged_correlation` | IP-3 |
| **IP-5** | Detector `cointegration` + `pair_spread` | IP-3 |
| **IP-6** | `TrialLedger` + pipeline validación | IP-1 |
| **IP-7** | Walk-forward rolling + purging/embargo | IP-6 |
| **IP-8** | Deflated Sharpe Ratio | IP-6 |
| **IP-9** | Pair backtester (2 piernas) | IP-5 |
| **IP-10** | API `/api/lab/pairwise/*` | IP-4, IP-6 |
| **IP-11** | UI scanner tab Pares | IP-10 |
| **IP-12** | Monte Carlo robustez pares | IP-9 |

---

## IP-0 — Documentación ✅

**Verificación:**

```bash
test -f docs/scanner/pairwise/AUDIT.md && \
test -f docs/scanner/pairwise/DESIGN.md && \
test -f docs/scanner/pairwise/IMPLEMENTATION_PLAN.md && echo OK
```

**Regresión:** Ninguna (solo docs).

---

## IP-1 — Contrato AlphaSignal + DetectorRegistry

**Archivos:**

- `research/alpha/models.py` — añadir `AlphaSignal`, enums `SignalScope`, `SignalDirection`
- `research/alpha/detectors/base.py`
- `research/alpha/detectors/registry.py`
- `tests/unit/research/test_alpha_signal_contract.py`
- `tests/unit/research/test_detector_registry.py`

**Verificación:**

```bash
uv run pytest tests/unit/research/test_alpha_signal_contract.py \
             tests/unit/research/test_detector_registry.py -q
uv run mypy --strict src/quantlab/research/alpha/models.py \
             src/quantlab/research/alpha/detectors/
```

**Criterio éxito:** ≥ 8 tests verdes; registry registra detector dummy; `AlphaSignal.to_dict()` round-trip.

**Regresión:**

```bash
uv run pytest tests/unit/research/test_alpha_features_f3.py -q
```

---

## IP-2 — Adapter legacy + normalización

**Archivos:**

- `research/alpha/detectors/adapters/legacy_profile.py`
- `research/alpha/normalization.py`
- `tests/unit/research/test_alpha_normalization.py`
- `tests/unit/research/test_legacy_profile_detector.py`

**Verificación:**

```bash
uv run pytest tests/unit/research/test_alpha_normalization.py \
             tests/unit/research/test_legacy_profile_detector.py -q
```

**Criterio éxito:** `legacy_v1` via detector produce mismos top-N que `AlphaScanner` en fixture sintético (±1e-9 composite).

---

## IP-3 — Universo pares + alineación

**Archivos:**

- `research/alpha/pairwise/universe.py` — `generate_pair_candidates(universe, max_pairs, min_liquidity)`
- `research/alpha/pairwise/align.py` — `align_pair_bars(bars_a, bars_b)`
- `research/alpha/pairwise/costs.py` — `estimate_pair_cost_bps(venue, market_type)`
- `tests/unit/research/test_pairwise_universe.py`

**Verificación:**

```bash
uv run pytest tests/unit/research/test_pairwise_universe.py -q
```

**Criterio éxito:** 15 símbolos → ≤ `max_pairs` candidatos; barras alineadas mismo length; sin timestamps futuros.

---

## IP-4 — Detector lagged_correlation

**Archivos:**

- `research/alpha/detectors/lagged_correlation.py`
- `research/alpha/detectors/contemporary_correlation.py`
- `tests/unit/research/test_lagged_correlation_detector.py`

**Verificación:**

```bash
uv run pytest tests/unit/research/test_lagged_correlation_detector.py -q
```

**Criterio éxito:**

- Fixture sintético con lag conocido (B sigue A con lag=3) → detector reporta lag=3 entre top signals.
- Con 100 lags falsos + 1 verdadero → solo verdadero pasa FDR (q<0.10).
- `min_bars=500` rechaza series cortas con `data_quality.insufficient_history`.

---

## IP-5 — Detectores cointegration + pair_spread

**Archivos:**

- `research/alpha/detectors/cointegration.py`
- `research/alpha/detectors/pair_spread.py`
- `tests/unit/research/test_cointegration_detector.py`

**Verificación:**

```bash
uv run pytest tests/unit/research/test_cointegration_detector.py -q
```

**Criterio éxito:**

- Serie I(1) sintética cointegrada (random walk común) → ADF p < 0.05.
- Series independientes → rechazadas.
- half_life calculado en rango esperado fixture.

**Dependencia:** añadir `scipy` a `pyproject.toml` si no presente.

---

## IP-6 — TrialLedger + validation pipeline

**Archivos:**

- `research/alpha/validation/trial_ledger.py`
- `research/alpha/validation/pipeline.py`
- `tests/unit/research/test_trial_ledger.py`
- `tests/unit/research/test_validation_pipeline.py`

**Verificación:**

```bash
uv run pytest tests/unit/research/test_trial_ledger.py \
             tests/unit/research/test_validation_pipeline.py -q
```

**Criterio éxito:**

- Pipeline rechaza mezclar `sharpe` en fase detect (assertion).
- Ledger cuenta N trials = pares × lags × windows del scan fixture.

---

## IP-7 — Walk-forward rolling + purging

**Archivos:**

- `research/alpha/validation/walk_forward_eval.py`
- Integración con `validation/splits.py`
- `tests/unit/research/test_pairwise_walk_forward.py`

**Verificación:**

```bash
uv run pytest tests/unit/research/test_pairwise_walk_forward.py -q
```

**Criterio éxito:** ≥ 3 folds en serie 2000 barras; embargo ≥ lookback; test nunca solapa train.

---

## IP-8 — Deflated Sharpe Ratio

**Archivos:**

- `research/alpha/validation/deflated_sharpe.py`
- `tests/unit/research/test_deflated_sharpe.py`

**Verificación:**

```bash
uv run pytest tests/unit/research/test_deflated_sharpe.py -q
```

**Criterio éxito:** Con n_trials=100 y sharpe observado moderado → DSR < sharpe observado.

---

## IP-9 — Pair backtester

**Archivos:**

- `research/strategies/pair_spread_strategy.py`
- `backtester/pair_engine.py` (o extensión `bar_based.py`)
- `tests/unit/backtester/test_pair_backtest.py`

**Verificación:**

```bash
uv run pytest tests/unit/backtester/test_pair_backtest.py -q
```

**Criterio éxito:** Long A + short B hedge_ratio=1 en fixture mean-reverting spread → equity crece vs buy-hold individual.

---

## IP-10 — API pairwise

**Archivos:**

- `workbench/lab_services.py` — `run_pairwise_lab_scanner`, `run_pairwise_lab_pipeline`
- `workbench/api.py` — handlers POST
- `tests/unit/workbench/test_pairwise_scanner_api.py`

**Verificación:**

```bash
uv run pytest tests/unit/workbench/test_pairwise_scanner_api.py -q
```

**Criterio éxito:** POST con fixture mock devuelve `signals[]` scope=pair; `include_signals=false` idéntico a scanner actual.

**Regresión:**

```bash
uv run pytest tests/unit/workbench/test_binance_lab_f111.py -q
```

---

## IP-11 — UI scanner tab Pares

**Archivos:**

- `static/js/panes/scanner.js` — toggle + tab
- `static/js/api.js` — `pairwiseScanner()`

**Verificación manual:**

1. `uv run quantlab-workbench`
2. Scanner → Modo pares ON → Ejecutar
3. Tab Pares muestra tabla (par, lag, score, confidence)
4. Scanner modo individual sin cambios

**Regresión automática:** tests IP-10.

---

## IP-12 — Monte Carlo robustez (opcional fase 2)

**Archivos:** extensión `montecarlo/` para shocks en hedge_ratio y spread.

**Verificación:**

```bash
uv run pytest tests/unit/montecarlo/test_pairwise_mc.py -q
```

---

## Gate final (por fase de producto)

Antes de certificar integración pairwise:

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest -q
```

---

## Orden de ejecución inmediato

1. ✅ IP-0 docs
2. 🔄 **IP-1** (en curso) — contrato + registry
3. IP-2 adapter legacy
4. IP-3 universo pares
5. IP-4 lagged_correlation
6. IP-6 trial ledger (paralelo posible con IP-4)
7. IP-5 cointegration
8. IP-7..IP-10
9. IP-11 UI

---

## Commits sugeridos (restauración)

| Tag / commit | Momento |
|--------------|---------|
| `restore/pre-pairwise-integration-20260812` | ✅ Antes de empezar |
| `feat(pairwise): IP-1 signal contract + registry` | Tras IP-1 verde |
| `feat(pairwise): IP-4 lagged correlation detector` | Tras IP-4 |
| … | Una fase verificable por commit |

---

*Plan listo. Implementación iniciada en IP-1.*
