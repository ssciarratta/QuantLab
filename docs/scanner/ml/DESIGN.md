# DESIGN.md — Módulo ML (GBM) scoring de candidatas

**Fecha:** 2026-08-12  
**Prerequisito:** `AUDIT.md`  
**Librería v1:** **LightGBM** (preferida: rápido, categorical-friendly). XGBoost = alternativa si LightGBM no instala bien en Windows; no ambas a la vez.  
**No:** redes neuronales en esta fase.

---

## 0. Decisiones cerradas

| ID | Decisión |
|----|----------|
| M1 | `signal_type=ml_ranking` dentro de `AlphaSignal` — no caso especial |
| M2 | Features solo desde señales/componentes ya persistidos |
| M3 | Target = outcome de `validate_candidate` (no retorno bruto) |
| M4 | Inferencia complementa Ranking A; no lo reemplaza |
| M5 | Inferencia **también** debe poder pasar por `validate_candidate` + DSR como cualquier candidata |
| M6 | `research/alpha/ml/` desacoplado: lee datos, no importa scanners/pairwise internos |
| M7 | Modelo inactivo si N_train < umbral o artefacto ausente (fail-closed) |

---

## 1. Ubicación

```
research/alpha/ml/
  features.py    # vector desde AlphaSignal / scan rows persistidos
  dataset.py     # join features(t) ↔ label(t→t+H) desde alpha_trials (+ bootstrap)
  train.py       # fit GBM + métricas modelo + manifest
  model.py       # carga artefacto → produce AlphaSignal ml_ranking
  registry.py    # versión activa / inactive
  splits.py      # walk-forward tabular + purge/embargo por horizonte
```

Acoplamiento permitido: contratos `AlphaSignal`, `TrialLedger`, paths `experiments/`.  
Prohibido: llamar detectores pairwise o FeatureCalculator “por la puerta de atrás” con barras crudas dentro de `ml/`.

*(Nota: el prompt menciona `scanners/` — en QuantLab el scanner vive en lab_services + detectors; no crear carpeta `scanners/` solo por el diagrama.)*

---

## 2. Target (exacto)

**Definición v1 (binario):**

> En el momento del scan `t`, para candidata `c` y estrategia default `s(c)`  
> (individual: 1ª recomendada del perfil / `momentum`; par: `recommend_strategy_for_signal`),  
> el label `y=1` sii la corrida `validate_candidate` en la **ventana siguiente**  
> (barras OOS con embargo) resultó `validated=True`  
> (hoy: `deflated_sharpe >= 0.95` y `sharpe_net > 0`).

**No usar:** retorno bruto, PnL %, Sharpe in-sample del scanner.

**Label suave opcional (fase posterior):** ranker con target = `deflated_sharpe` clipado — **no en v1**.

**Estrategia default fija en el manifest** del dataset (reproducibilidad). Cambiar default = nuevo dataset_id.

---

## 3. Esquema de features (v1 — solo existentes)

### Individual

| Feature | Origen |
|---------|--------|
| `norm_composite` | `normalized_score` del AlphaSignal individual |
| `confidence` | cobertura factores |
| `comp_<name>` | `components[].normalized` si existe (volatility, volume, liquidity, momentum, …) |
| `profile` | categorical: signal_type / profile |
| `timeframe` | categorical |
| `market_type` | spot/futures |

### Pair

| Feature | Origen |
|---------|--------|
| `norm_score` | `normalized_score` |
| `confidence` | detector |
| `lag` | si aplica (0 si null) |
| `meta_hedge_ratio`, `meta_adf_pvalue`, `meta_half_life`, `meta_spread_z`, `meta_estimated_cost_bps` | metadata |
| `signal_type` | categorical (corr / lag / coint / spread) |
| `timeframe`, `market_type` | |

Missing → NaN / categorical missing que LightGBM maneja; **no** imputar con 0 fingiendo “disponible” (misma filosofía que FeatureCalculator).

Schema versionado: `feature_schema_version = "ml-features-v1"` en manifest.

---

## 4. Splits de entrenamiento

```
Tiempo →
[ block_1 train | purge H | block_1 test ]
[ block_2 train | purge H | block_2 test ]
...
```

- Ordenar filas por `scan_timestamp`.  
- Horizonte `H` = embargo en **unidades de scan** (o barras equivalentes documentadas), ≥ embargo de `validate_candidate`.  
- Dentro de train: validación interna LightGBM (early stopping) en un **último tramo temporal** del train, no random.  
- Reportar: AUC, precision@k, recall de clase positiva, feature importance.  
- **Separado:** después, señales `ml_ranking` top-N pasan por Ranking A → usuario elige → `validate_candidate` (evaluación de estrategia / DSR).

---

## 5. Inferencia (research)

1. Scanner corre (individual y/o pairwise) → candidatas.  
2. `ml.model.score_candidates(signals)` → nuevas `AlphaSignal(signal_type=ml_ranking, raw_score=proba, normalized_score=percentil entre ml_ranking)`.  
3. Se listan **junto** a otras señales en Ranking A (no sustituyen composite legacy).  
4. Top-N a validar sigue la metodología v3 (1 estrategia/corrida).

UI: checkbox **ML ranking** (default ON). Primer escaneo hace bootstrap sintético; cada Validar alimenta y reentrena.

---

## 6. Versionado

Por entrenamiento, bajo `experiments/alpha_ml/{model_id}/`:

- `manifest.json` — deriva de campos `ExperimentManifest` + hyperparams + `feature_schema_version` + git commit + `n_train`/`n_pos`/`n_neg` + métricas  
- `model.txt` / `model.joblib` — artefacto LightGBM  
- `metrics.json` — AUC, PR, importance  

`registry.py`: `active_model_id` o `None` (inactivo).

---

## 7. Fuera de alcance

- LSTM/TCN/DL  
- Features ad hoc desde klines dentro de `ml/`  
- LIVE / order routing  
- Reemplazar scanner  
- Entrenar si N_pos < umbral (ej. 30) — documentar y abortar
