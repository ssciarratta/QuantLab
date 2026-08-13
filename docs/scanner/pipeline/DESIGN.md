# DESIGN.md — Cerrar el pipeline Alpha (simple)

**Fecha:** 2026-08-12  
**Prerequisito:** `AUDIT.md`  
**Principio:** Paridad de calidad con pares, **menos** superficie. Nada que no cambie “¿entra la candidata?” o “¿se valida la estrategia?”.

---

## 0. Decisiones de diseño (cerradas)

| ID | Decisión | Motivo |
|----|----------|--------|
| D1 | Unificar salida individual → `AlphaSignal` | Contrato único con pares |
| D2 | No agregar features nuevas | Features ya existen; falta rigor de salida |
| D3 | Un solo `validate_candidate` para individual y par | Evitar dos caminos de validación |
| D4 | Separar rankings Candidatos / Estrategias validadas | Corrección #1 del audit §6 |
| D5 | Ledger persistente de **toda** corrida de validación | DSR honesto |
| D6 | No tocar detectores pairwise | Solo consumir pipeline compartido |
| D7 | Recomendación de estrategia ≠ ranking validado | Sugerencia heurística; no decide |

---

## 1. Scanner individual — paridad (sin inflar)

### 1.1 Contrato de salida (obligatorio)

Misma forma que pares:

```
AlphaSignal:
  signal_id, timestamp, signal_type, scope=individual,
  symbols=(one,), direction, raw_score, confidence?,
  lookback, timeframe, metadata, normalized_score
```

**Cómo (mínimo):**

1. Tras `score_with_profile` / `AlphaScanner.scan`, mapear a `AlphaSignal` vía adapter existente (`LegacyProfileDetector` o `from_ranked_candidate`).
2. Aplicar `percentile_rank_signals` (ya en `normalization.py`) → `normalized_score`.
3. `confidence` simple y fija: p.ej. fracción de factores disponibles en el perfil (0–1). **No** p-values inventados.
4. API/UI del Scanner individual puede seguir mostrando tabla “friendly”, pero el payload canónico incluye `signals[]` (como pairwise).

**No hacer:** nuevos detectores, nuevos perfiles, Kronos dentro de este contrato.

### 1.2 Qué NO cambia en el ranking de candidatos

El `raw_score` / composite sigue saliendo de features conocidas al escanear.  
**Prohibido** meter Sharpe, PnL, DSR, returns en el score de selección.  
Reusar `assert_no_selection_leakage` en el path individual (hoy solo conceptual en pairwise).

---

## 2. Validación de estrategias — un solo camino

```
Candidata (AlphaSignal: individual | pair)
        │
        ▼
validate_candidate(signal, strategy_id, params)   # UNA estrategia, UNA config
        │
        ▼
Backtest con costos netos (fees / slippage / funding según market_type)
        │
        ▼
Train / test con walk_forward_with_embargo (reusar walk_forward_eval.py)
        │
        ▼
TrialLedger.append(ALWAYS)  → experiments/alpha_trials/*.jsonl
        │
        ▼
Sharpe neto → Deflated Sharpe(N = ledger.count())
        │
        ▼
si validated → ranking de estrategias validadas
```

### 2.1 Reglas duras

- Misma función para candidata individual o par (rama interna solo para armar barras/piernas).
- **Una** estrategia por llamada. Comparar estrategias = N llamadas = N trials en el ledger.
- Registrar **siempre** (ok / fail / sharpe negativo).
- No crear `validate_pair` / `validate_individual` públicos distintos.

### 2.2 Umbral (simple, un solo knocker)

Reusar el de `ValidationPipeline`: `dsr >= 0.95` y `sharpe_net > 0` (ajustable después; no parametrizar en UI en v1).

### 2.3 Qué deprecar / no usar como “validación”

| Hoy | Rol nuevo |
|-----|-----------|
| `run_binance_pipeline` | Puede llamar a `validate_candidate` en loop top-N; deja de ser “la” verdad |
| `strategy_rank` | Queda como **exploración research** etiquetada; **no** alimenta ranking validado |
| Optimize grid | Exploración; cada trial debe poder loguearse si se usa para decidir |
| Simulador | Sandbox; handoff hacia `validate_candidate` opcional (fase posterior UI) |

---

## 3. Separación dura de rankings

| Ranking | Quién lo arma | Inputs permitidos | Inputs prohibidos |
|---------|---------------|-------------------|-------------------|
| **A — Candidatos** | Scanner (individual o pairwise) | Features / detectores / percentil | Sharpe, PnL, DSR, returns de BT |
| **B — Estrategias validadas** | `ValidationPipeline.rank_validated` | Resultados de `validate_candidate` | Scores del scanner |

**UI / metodología (sin código complejo):**

- Dos listas, nunca un score compuesto fusionando moneda+par+estrategia.
- Decidir con ranking **B**. Ranking **A** solo elige qué mandar a validar (top-N fijo).
- `recommended_strategy` / `attach_recommendations` = hint (D7), no fila de ranking B.

---

## 4. Persistencia

| Store | Contenido |
|-------|-----------|
| `experiments/alpha_scans/` | Snapshots de ranking A (como hoy) |
| `experiments/alpha_trials/` **nuevo** | JSONL append-only: toda corrida de validación (win/lose) |
| Ranking B | Vista derivada del ledger (archivo o endpoint read-only) |

Campos mínimos por trial: `trial_id`, `opportunity_id`, `scan_id`, `signal_id`, `scope`, `symbols`, `strategy_id`, `params_hash`, `sharpe_net`, `deflated_sharpe`, `validated`, `status`, `n_trials_at_eval`, `created_at`, `ok`, `error?`.

---

## 5. Walk-forward

- Path de `validate_candidate`: split 70/30 + embargo (mín. 2; se recorta para no vaciar el test).
- `walk_forward_with_embargo` (rolling) existe para eval pairwise; no es el default de Validar.
- Defaults fijos; **no** 5 knobs en UI.

---

## 6. Metodología de uso (producto, no código)

1. Scanner individual y pares **separados**; mirar juntos sin fusionar scores.  
2. Validar solo top-N fijo (5–10).  
3. Una candidata × una estrategia por corrida.  
4. Cadencia fija de escaneo.  
5. Decidir con ranking B.

---

## 7. Fuera de alcance (explícito)

- Nuevas señales / factores.  
- Cross-venue pairs.  
- LIVE / order routing.  
- Reescribir motor de pares.  
- Fusionar listas individual+par en un meta-score.  
- UI rediseño grande (solo lo mínimo para ver ranking B y disparar validate).
