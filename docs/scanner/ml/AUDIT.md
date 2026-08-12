# AUDIT.md — Módulo ML (GBM) para scoring de candidatas

**Fecha:** 2026-08-12  
**Prompt:** Maestro v4  
**Scope:** Solo 4 puntos. No reauditar pairwise ni pipeline v3.  
**Restore point previo:** `restore/pre-ml-gbm-20260812` @ `c37f5df`

---

## 1. Features / señales normalizadas disponibles hoy (superficie de entrada)

**Contrato canónico:** `AlphaSignal` (`models.py`) con `raw_score`, `normalized_score` (percentil), `confidence`, `metadata`, `scope`, `signal_type`.

### Scanner individual (`scope=individual`)

| Fuente | Qué sale como feature usable | Evidencia |
|--------|------------------------------|-----------|
| Perfiles / `CompositeScorer` | Factores: volatility, volume, liquidity, momentum, trend_quality, spread, depth, funding, OI, persistence (raw + normalized en `components[]`) | `features.py`, `scoring.py`, `profiles.py` |
| Export lab | `signals[]` via `individual_export.attach_individual_signals` → `normalized_score` percentil + `confidence` = cobertura de factores | `individual_export.py` |
| Persistencia scan | `experiments/.../alpha_scans/*.json` — rows/scores (y pairwise signals) | `persist.py` / `ScanStore` |

### Módulo pares (`scope=pair`)

| `signal_type` | Score / metadata típica |
|---------------|-------------------------|
| `contemporary_correlation` | corr → raw/normalized |
| `lagged_correlation` | lag, corr rezagada, FDR |
| `cointegration` | hedge_ratio, adf_pvalue, half_life |
| `pair_spread` | spread_z, estimated_cost_bps |
| + `recommended_strategy` | hint (no feature de mercado) | `pairwise/recommend.py` |

**Veredicto entrada ML:** la superficie correcta es **vectores ensamblados desde `AlphaSignal` + `components`/`metadata` ya persistidos**, no OHLCV crudo.  
**No inventar features nuevas en v1** (restricción del prompt). Si falta algo, primero al scanner.

---

## 2. ¿Hay histórico con outcome conocido para entrenamiento supervisado?

| Store | Contenido | ¿Outcome (validado / Sharpe neto)? |
|-------|-----------|-------------------------------------|
| `alpha_scans/` | Snapshot Ranking A (candidatas) | **No** — solo scores de selección |
| `alpha_trials/trials.jsonl` | Corridas `validate_candidate` (win+lose) | **Sí** — `validated`, `sharpe_net`, `deflated_sharpe`, `strategy_id`, `signal_id`, `symbols` | `validate_candidate.py`, `trial_ledger.py` |
| ExperimentRegistry / reports | Backtests lab genéricos | Parcial; no ligado 1:1 a señal scanner |

**Veredicto:** El target supervisado viable es el ledger de **`alpha_trials`**, no `alpha_scans` solo.  
**Gap crítico:** el ledger es **nuevo (pipeline v3)** → en sesiones reales puede haber **pocas filas** al día 0. Antes de entrenar en “prod research” hace falta:

1. Generar dataset sintético/fixture para tests, y/o  
2. Bootstrap de labels vía `validate_candidate` offline sobre scans históricos (script de labeling, fase de implementación).

Sin N mínimo de trials etiquetados, el GBM no debe activarse en el ranking (fail-closed / modelo inactivo).

---

## 3. ¿Hay tracking de experimentos ML?

| Qué hay | Qué no hay |
|---------|------------|
| `ExperimentManifest` core (`core/types/manifests.py`) — seed, commit, config, datasets | **MLflow / W&B** no en deps |
| `ExperimentRegistry` SQLite (`experiments/registry.py`) | No hay carpeta `research/alpha/ml/` |
| Strategies UI `xgboost` / `lightgbm` = **proxies** de features, **sin modelo entrenado** | `pyproject.toml`: **sin** lightgbm/xgboost |

**Veredicto:** Definir tracking **desde cero** siguiendo `ExperimentManifest` + sidecar JSON bajo `experiments/alpha_ml/` (versión modelo, hyperparams, feature schema hash, métricas AUC, path artefacto). No introducir MLflow en v1 salvo necesidad explícita.

---

## 4. ¿Splits purging/embargo reutilizables para entrenar el GBM?

| Pieza | Uso actual | ¿Sirve para ML? |
|-------|------------|-----------------|
| `walk_forward_eval.split_bars_train_test` + embargo | Validación de **estrategia** sobre barras | Temporal OK para series, pero ML necesita filas (candidata×t) |
| `ValidationPipeline` + DSR | Evalúa **señal ya candidata** post-backtest | **Post-inferencia** — no sustituye train/val del modelo |
| Purging entre overlapping labels | No hay dataset tabular ML aún | **Hay que adaptar** |

**Particularidades supervisadas:**

- Cada fila = candidata en `t` con features de scan en `t` y label de outcome en ventana `(t, t+H)`.
- Labels de ventanas solapadas → **purging** entre train y test (embargo ≥ horizonte H).
- Clases desbalanceadas (`validated=True` suele ser minoritaria) → split estratificado **dentro** de bloques temporales, no shuffle aleatorio global.
- Walk-forward de **reentrenamiento** del GBM ≠ walk-forward de validación de estrategia (son dos loops; DESIGN los separa).

**Veredicto:** Reusar el **criterio temporal + embargo** del pipeline; **no** reusar tal cual el API de barras. El módulo `ml/` define splits sobre el **dataset tabular** (filas señal+label) con purge por horizonte.

---

## Resumen ejecutivo

1. Entrada = señales normalizadas ya existentes (individual + pairwise).  
2. Labels = `alpha_trials` (validated/DSR); scans solos no alcanzan; N puede ser bajo al inicio.  
3. Sin MLflow; versionar con `ExperimentManifest` + `experiments/alpha_ml/`.  
4. Splits temporales con purge propios del tabular; validación de estrategia (DSR) sigue siendo obligatoria **después** de emitir `ml_ranking`.
