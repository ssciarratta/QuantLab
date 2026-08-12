# AUDIT.md — Pipeline Alpha (scanner individual + validación de estrategias)

**Fecha:** 2026-08-12  
**Scope:** Solo los 6 puntos del Prompt Maestro v3.  
**Fuera de scope:** lógica interna del módulo pairwise (salvo contraste de contrato).  
**LIVE_BLOCKED:** True (no auditado aquí; se asume vigente).

---

## 1. Señales del scanner individual vs rigor del módulo de pares

**Qué tiene hoy el individual**

| Capa | Qué emite | Evidencia |
|------|-----------|-----------|
| Legacy | `AssetScore`: vol / volume / liquidity → `composite` min-max | `research/alpha/__init__.py` (~L24–198) |
| Features | + momentum, trend_quality, spread, depth, funding, OI, persistence | `features.py` L29–47 |
| Profiles | Pesos por familia (trend, momentum, MR, MM, funding…) | `profiles.py` L23–61 |
| Scoring | `CompositeScorer` + min-max (o robust) transversal | `scoring.py` L99–160, L266–274 |
| UI path | `run_binance_lab_scanner` / `run_venue_lab_scanner` → filas `composite` + `attach_recommendations` | `lab_services.py` ~L743–867 |

**Qué le falta frente a pares**

| Capacidad | Pares | Individual (path UI) |
|-----------|-------|----------------------|
| Contrato `AlphaSignal` | Sí | Adapter existe (`detectors/adapters/legacy_profile.py`) pero **no es el path del Scanner UI** |
| `normalized_score` percentil | `percentile_rank_signals` | No en respuesta API; usa min-max de factores → `composite` |
| `confidence` estadística | Sí (corr/ADF/etc.) | Ausente en scores UI |
| Trial ledger + DSR | `ValidationPipeline` | Solo en pairwise opcional |
| Validación OOS acoplada | Checkbox + fees | No en scanner individual |

**Veredicto:** Las features no son el cuello de botella. Falta **paridad de contrato + normalización percentil + confianza + registro de trials**. No hace falta inventar indicadores nuevos.

---

## 2. Contrato de salida — inconsistente

| Path | Contrato |
|------|----------|
| Scanner individual (lab) | `scores[]` con `instrument_id`, `composite`, componentes; + `recommendation` heurística |
| Pairwise | `AlphaSignal.to_dict()` + `recommended_strategy` |
| Adapter legacy (registry) | Ya produce `AlphaSignal` scope=individual | `legacy_profile.py` L39–60 |

`AlphaSignal.from_ranked_candidate` existe (`models.py` ~L184) pero el lab **no lo usa** al devolver el scan individual.

**Prioridad:** Unificar salida del individual a `AlphaSignal` (scope=individual) **antes** de agregar señales. El adapter legacy es el puente; no reescribir scoring.

---

## 3. Cómo se prueban estrategias sobre una candidata

**Hoy: varios caminos, ninguno es “validación limpia”.**

| Camino | Qué hace | Gaps |
|--------|----------|------|
| **Simulador** (handoff desde Scanner) | 1 moneda × 1 estrategia, fees VIP0 | Manual; no DSR; no ledger global |
| **`run_binance_pipeline`** | Scan top-N → misma `strategy_id` en todas → backtest OOS (split 70/30) | Una estrategia para N monedas; sin DSR; sin embargo; no registra trials fallidos de forma uniforme | `lab_services.py` L1780–2015 |
| **`strategy_rank`** | 1 moneda × ~37 estrategias → ranking por **PnL %** | Múltiples comparaciones sin DSR; mezcla “ranking de estrategias” con backtest in-sample típico | `research/sim/strategy_rank.py` L1–80 |
| **Optimize / grid** | Grid lookback×qty → maximiza Sharpe | Peor caso de múltiples trials | `lab_services.py` ~L2078 |
| **Pairwise `run_validation`** | Top señales → spread BT + DSR | Solo pares; ledger en memoria por corrida | `lab_services.py` ~L3642+ |

**Veredicto:** No hay un pipeline único repetible “candidata → 1 estrategia → costos → purged WF → registro siempre → DSR → ranking validado”.

---

## 4. `walk_forward.py` — ¿purging y embargo?

| Módulo | Comportamiento |
|--------|----------------|
| `research/alpha/walk_forward.py` | Split **plano** rank_fraction default **0.70**; sin purge, sin embargo | L34–87 |
| `research/alpha/validation/walk_forward_eval.py` | Rolling + **embargo** post-train | L20–47 |
| Uso en pipeline Binance | Solo el split plano | `lab_services.py` L1860–1868 |
| Uso en pairwise validation | Cut 70% sobre closes alineados (también plano) | `lab_services.py` ~L3640 |

**Veredicto:** El walk-forward “oficial” del lab individual es **70/30 sin purging/embargo**. El módulo con embargo existe pero **no está cableado** al path de estrategias puntuales.

---

## 5. `experiments/alpha_scans/` — ¿todas las pruebas?

| Qué persiste | Contenido |
|--------------|-----------|
| `ScanStore.save_scored` | Snapshot del **ranking del scan** (filas/scores o señales pairwise top) | `persist.py` L154–197 |
| Path | `session.experiments_dir / "alpha_scans"` | `api.py` ~L1323, L1379 |
| Trials de validación | `TrialLedger` JSONL **opcional**; en pairwise se instancia **sin path** → solo memoria de la corrida | `trial_ledger.py`; `lab_services` pairwise |
| Backtests fallidos / Sharpe bajos | No hay ledger global de “estrategia × candidata × resultado” | — |

**Veredicto:** `alpha_scans/` guarda **candidatos del scanner**, no el universo completo de trials de validación. Sin registro de ganadoras **y** perdedoras de estrategias, el **N del Deflated Sharpe no es honesto** fuera de una corrida pairwise aislada.

---

## 6. Leakage ranking candidatos ↔ backtest (sospecha raíz)

### A) ¿El score del scanner individual usa Sharpe/PnL?

**No en el path de scoring puro.**  
`CompositeScorer` / `AlphaScanner` solo usan features de mercado.  
`ValidationPipeline.assert_no_selection_leakage` prohíbe `sharpe`/`pnl` en scores de selección (`pipeline.py` L95–101) — pero **solo se usa en tests/pairwise**, no en el lab scanner individual.

### B) ¿Dónde sí se mezcla conceptualmente?

| Síntoma | Evidencia |
|---------|-----------|
| Pipeline empaqueta scanner + backtests en un solo resultado | `kind: binance_pipeline` con `scanner` + `backtests` | L2004–2015 |
| Ranking de estrategias por PnL sobre muchos trials | `strategy_rank.py` ordena por `pnl_pct` sin DSR | L70–78 |
| Recomendaciones del scanner sugieren estrategias **antes** de validar | `attach_recommendations` / `recommend_for_score` | `recommend.py` L213–278 |
| UI puede inducir a “operar el top del scanner” | Metodología actual no distingue ranking candidatos vs ranking validado | Scanner pane |

### C) Leakage temporal suave (no Sharpe en score, pero sí selección in-sample)

Si `walk_forward=False` en pipeline: **misma ventana** rank + backtest (`lab_services.py` L1870–1878).  
Con WF=True: ranking solo en tramo early — **correcto a medias**, pero sin embargo.

**Veredicto leakage:**  
- **Hard leakage (Sharpe dentro del composite del scanner):** no confirmado.  
- **Soft leakage / confusión de rankings:** **sí** — pipeline + strategy_rank + recommendations mezclan “qué moneda es interesante” con “qué estrategia rindió”, y no hay ranking final de estrategias **validadas** separado y persistido.

**Prioridad #1 del diseño:** separación dura de rankings + un solo pipeline de validación con ledger persistente.

---

## Resumen ejecutivo (6 bullets)

1. Individual tiene features suficientes; le falta contrato/confianza/percentiles/ledger del nivel pares.  
2. Contratos inconsistentes: scores/`composite` vs `AlphaSignal` — unificar primero.  
3. Estrategias: caminos ad hoc (Sim, pipeline, strategy_rank, grid); no hay pipeline único.  
4. `walk_forward.py` = split 70/30; embargo solo en `walk_forward_eval.py` (no cableado).  
5. `alpha_scans/` = scans, no trials de validación; DSR no puede ser honesto a escala.  
6. No hay Sharpe en el composite; sí hay mezcla de rankings y ranking de estrategias por PnL sin DSR — esa es la causa raíz a corregir primero.

---

## No-touch confirmado

Módulo pairwise: no requiere cambios internos salvo **consumir el mismo ValidationPipeline persistente** cuando exista el path unificado (punto de integración, no reescritura de detectores).
