# Fase 1 — Diseño: Integración Pairwise/Cointegración al Alpha Scanner

**Fecha:** 2026-08-12  
**Prerequisito:** `AUDIT.md` (Fase 0)  
**Estado:** Propuesto para implementación — defaults operativos donde producto está abierto

---

## 0. Decisiones de producto (RESUELTAS 2026-08-12)

| ID | Pregunta | Decisión usuario | Implicancia |
|----|----------|------------------|-------------|
| P1 | Spot / Futures / ambos | **Ambos** ✓ | `run_pairwise_lab_scanner(market_type=spot\|futures)` + `list_futures_symbols` |
| P2 | Mismo exchange vs cross-venue | **Mismo venue** (no cross) | Pares solo dentro Binance spot o Binance futures |
| P3 | Lag vs cointegración | **Ambos** (ver tabla abajo) | Todos los detectores activos; usuario elige cuál priorizar |
| P4 | Monedas / estrategias / ambas | **Ambas** ✓ | `recommended_strategy` en API + handoff Sim (`recommend.py`) |

### P3 — Qué es cada señal

| Señal | Qué mide | Cuándo usarla | Estrategia típica |
|-------|----------|---------------|-------------------|
| **Correlación contemporánea** | A y B se mueven juntos en la misma ventana | Filtro inicial / redundancia | Beta hedge, basket |
| **Correlación rezagada (lag)** | B sigue a A con X velas de retraso | Lead-lag, momentum relativo | `pairs_lag`, relative strength |
| **Cointegración** | Relación estable de largo plazo; spread estacionario | Mean-reversion estructural | Pair trading long-short |
| **Pair spread (z-score)** | Spread muy alejado de su media | Timing de entrada (si ya hay cointegración) | Entrada/salida z-score |

**Orden sugerido al leer resultados:** cointegración → spread z → lag → correlación (solo filtro).

---

## 1. Arquitectura modular de detectores

### 1.1 Organización real (adaptada a QuantLab, no impuesta)

QuantLab hoy usa `research/alpha/` plano. **Extensión propuesta:**

```
src/quantlab/research/alpha/
├── models.py                    # existente + AlphaSignal (nuevo)
├── profiles.py                  # existente — legacy detectores vía adapter
├── scoring.py                   # existente — normalización individual
├── detectors/                   # ★ NUEVO
│   ├── __init__.py
│   ├── registry.py              # DetectorRegistry + decorador @register
│   ├── base.py                  # DetectorProtocol, DetectorContext
│   ├── adapters/
│   │   └── legacy_profile.py    # wrap build_profile → detector individual
│   ├── lagged_correlation.py    # NUEVO
│   ├── cointegration.py           # NUEVO
│   ├── pair_spread.py           # NUEVO (z-score spread, half-life)
│   └── contemporary_correlation.py # NUEVO (baseline)
├── pairwise/                    # ★ NUEVO — orquestación pares
│   ├── __init__.py
│   ├── universe.py              # generación pares candidatos (filtros)
│   ├── align.py                 # alineación temporal multi-serie
│   └── costs.py                 # costo estimado 2 piernas
├── normalization.py             # ★ NUEVO — percentiles transversales
├── ranking.py                   # existente implícito en scoring — extender pairs
├── validation/                  # ★ NUEVO (separado de validation/ global)
│   ├── __init__.py
│   ├── pipeline.py              # selección → BT → métricas → DSR
│   ├── trial_ledger.py          # conteo trials
│   └── deflated_sharpe.py
└── walk_forward.py              # existente — extender para rolling eval
```

**Principio:** No mover `profiles.py` ni `AlphaScanner`; los detectores legacy se registran vía `LegacyProfileDetector`.

### 1.2 DetectorProtocol

```python
@dataclass(frozen=True)
class DetectorContext:
    bars_by_instrument: Mapping[str, Sequence[Bar]]
    timeframe: str
    lookback_bars: int
    venue: str
    market_type: str
    as_of: datetime | None
    config: dict[str, Any]

class AlphaDetector(Protocol):
    detector_id: str
    signal_type: str
    scope: Literal["individual", "pair", "group"]

    def required_min_bars(self) -> int: ...
    def detect(self, ctx: DetectorContext) -> tuple[AlphaSignal, ...]: ...
```

Cada detector:

- Autocontenido, sin estado mutable compartido.
- Declara `required_min_bars()`.
- Activable vía `DetectorRegistry.enabled` + config YAML/JSON en request API.
- Registrado con `@register_detector("lagged_correlation")` — **sin editar archivo central**.

### 1.3 Registry

```python
class DetectorRegistry:
    def register(self, detector: AlphaDetector) -> None: ...
    def get(self, detector_id: str) -> AlphaDetector: ...
    def list_enabled(self, config: DetectorRunConfig) -> tuple[AlphaDetector, ...]: ...
    def run_all(self, ctx: DetectorContext, config) -> tuple[AlphaSignal, ...]: ...
```

Detectores legacy (`legacy_v1`, `momentum`, …) = `LegacyProfileDetector(profile_name)` → emite `AlphaSignal` scope=individual mapeando `ScoredRow`.

---

## 2. Contrato de salida estandarizado

### 2.1 `AlphaSignal` (nuevo)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `signal_id` | `str` | UUID determinista o hash(canonical) |
| `timestamp` | `datetime` | Momento generación (última barra usada) |
| `signal_type` | `str` | `momentum`, `lagged_correlation`, `cointegration`, … |
| `scope` | `str` | `individual` \| `pair` \| `group` |
| `symbols` | `tuple[str, ...]` | 1+ símbolos / instrument_ids |
| `direction` | `str` | `long` \| `short` \| `long-short` \| `neutral` |
| `raw_score` | `float` | Intensidad original |
| `confidence` | `float \| None` | p-value invertido o 1-p (mayor = más confiable) |
| `lookback` | `int` | Ventana en barras |
| `lag` | `int \| None` | Retraso detectado |
| `timeframe` | `str` | ej. `1h` |
| `data_quality` | `dict` | flags, completeness, gap_events |
| `metadata` | `dict` | hedge_ratio, half_life, adf_pvalue, corr, … |

### 2.2 Retrocompatibilidad

| Existente | Migración |
|-----------|-----------|
| `AssetScore` / `RankedCandidate` | `AlphaSignal.from_ranked_candidate(rc)` scope=individual |
| API `/api/lab/binance/scanner` | Sigue devolviendo `candidates[]`; añade opcional `signals[]` |
| `ScanStore` JSON | Campo nuevo `signals` en `result`; `candidates` sin cambio |
| UI `scanner.js` | Tab "Pares" consume `signals` filtradas scope=pair |

**Regla:** Si `include_signals=false` (default), comportamiento idéntico al actual.

---

## 3. Módulo lagged_correlation

### 3.1 Responsabilidades

1. Generar pares candidatos desde universo (mismo venue).
2. Para cada par (A, B):
   - Probar lags `L ∈ {0..L_max}` sobre retornos log o pct.
   - Calcular correlación en ventana rolling `W` (estabilidad).
   - Test significancia por lag (t-test aproximado o Fisher z).
3. **Corrección múltiple:** Benjamini-Hochberg FDR sobre todos (par, lag) probados.
4. Persistir solo candidatas con FDR q < 0.10 **y** estabilidad rolling (std corr across windows < threshold).
5. Estimar costo operativo vía `pairwise/costs.py`.

### 3.2 Prohibiciones (código)

- No seleccionar argmax correlación sin corrección.
- No usar mismo tramo para elegir lag y reportar score final sin split.

### 3.3 Parámetros default

```yaml
lagged_correlation:
  lags: [0, 1, 2, 3, 4, 5, 6, 12, 24]
  rolling_windows: [60, 120, 240]
  min_bars: 500
  fdr_alpha: 0.10
  min_abs_corr: 0.15
```

---

## 4. Módulo cointegration

### 4.1 Método elegido

| Decisión | Elección | Justificación |
|----------|----------|---------------|
| Hedge ratio | **OLS rolling** (v1); Kalman (v2) | Simple, auditable, suficiente para research |
| Test estacionariedad | **ADF sobre spread** (v1) | Univariado por par; Johansen reservado para grupos (fuera alcance) |
| Half-life | Regresión AR(1) sobre spread | Estándar pairs trading |

### 4.2 Salidas persistidas (metadata)

- `hedge_ratio`, `hedge_ratio_std` (rolling)
- `adf_pvalue`, `spread_z`, `half_life_bars`
- `regime_break`: bool si ADF falla en >30% ventanas rolling
- `residual_var`: varianza no explicada
- `liquidity_score`: min(liquidity_A, liquidity_B)
- `estimated_round_trip_cost_bps`

### 4.3 Criterio aceptación par

Par aceptado solo si:

- ADF p < 0.05 en ≥ 70% ventanas rolling
- |spread_z| < 4 (no extremo roto)
- half_life ∈ [5, 500] barras
- liquidez ambas piernas > umbral

---

## 5. Normalización transversal (`normalization.py`)

```python
def percentile_rank(
    signals: Sequence[AlphaSignal],
    *,
    group_by: tuple[str, ...] = ("timestamp", "timeframe", "scope", "signal_type"),
) -> tuple[AlphaSignal, ...]:
```

**Límites de agrupación obligatorios:**

- Fecha (día o bar timestamp según TF)
- Universo (scan_id)
- Timeframe
- Perfil / signal_type
- scope (individual vs pair — **nunca mezclar**)

Salida: campo `normalized_score ∈ [0, 1]` añadido (no reemplaza `raw_score`).

---

## 6. Separación selección vs evaluación (`validation/pipeline.py`)

```
┌─────────────────┐
│ DetectorRegistry│  ← solo raw features, sin Sharpe
└────────┬────────┘
         │ AlphaSignal candidatas
         ▼
┌─────────────────┐
│ TrialLedger.log │  ← cada (detector, par, lag, window) = 1 trial
└────────┬────────┘
         ▼
┌─────────────────┐
│ PairBacktester  │  ← retornos netos fees+slippage 2 piernas
└────────┬────────┘
         ▼
┌─────────────────┐
│ WalkForwardEval │  ← rolling folds + purging/embargo
└────────┬────────┘
         ▼
┌─────────────────┐
│ MetricsEngine   │  ← Sharpe neto, maxDD, stability
└────────┬────────┘
         ▼
┌─────────────────┐
│ DeflatedSharpe  │  ← n_trials desde TrialLedger
└────────┬────────┘
         ▼
   Ranking final validado (scope=pair)
```

**Invariante enforceable:**

```python
class ValidationPipeline:
    def rank_validated(self, signals, backtest_results) -> ...:
        # PROHIBIDO: usar backtest_results.sharpe como input a detect()
        ...
```

Sharpe del scanner **nunca** entra al composite del scanner.

### 6.1 Purging / embargo

```python
embargo_bars = max(lookback, half_life, holding_period)
# test_start >= train_end + embargo_bars
```

Implementar en `validation/pipeline.py` reutilizando `validation/splits.walk_forward`.

### 6.2 Deflated Sharpe Ratio

Implementación Bailey-López de Prado simplificada:

```python
def deflated_sharpe_ratio(
    observed_sharpe: float,
    n_trials: int,
    n_observations: int,
    skew: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
```

`n_trials` = `TrialLedger.count()` acumulado por sesión/experimento.

---

## 7. Alcance: pares primero

**In scope v1:**

- Pares same-venue spot USDT
- Detectores: contemporary_correlation, lagged_correlation, cointegration, pair_spread
- Evaluación walk-forward rolling (≥ 3 folds)
- Trial ledger + DSR

**Out of scope (fase posterior explícita):**

- Grupos / clustering / PCA / Johansen multivariado
- Cross-venue spreads
- Futures funding en hedge ratio
- LIVE routing

---

## 8. Integración API / UI

### 8.1 API nueva

| Ruta | Descripción |
|------|-------------|
| `POST /api/lab/pairwise/scanner` | Scan detectores pairwise |
| `POST /api/lab/pairwise/pipeline` | Scan → validate → rank |
| `GET /api/lab/detectors` | Catálogo detectores + min_bars |

Request extendido:

```json
{
  "venue": "binance",
  "market_type": "spot",
  "interval": "1h",
  "kline_limit": 720,
  "detectors": ["lagged_correlation", "cointegration"],
  "include_signals": true,
  "walk_forward": true
}
```

### 8.2 UI (`scanner.js`)

- Toggle "Modo pares" (off = comportamiento actual)
- Tab resultados: Individual | Pares
- Handoff Simulador con `pair: ["BN:BTCUSDT", "BN:ETHUSDT"]`

---

## 9. Dependencias

- `numpy` / `scipy` (ADF, stats) — verificar en `pyproject.toml`; añadir `scipy` si falta.
- Sin copiar código del repo referencia.

---

## 10. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Combitoria O(n²) pares | Top-N liquidez previo; cap `max_pairs=500` |
| kline_limit bajo | Gate `min_bars` + error claro en API |
| Romper scanner legacy | `include_signals=false` default; tests regresión |
| DSR sin trials honestos | TrialLedger obligatorio en pipeline |

---

*Fase 1 completada. Siguiente: `IMPLEMENTATION_PLAN.md`.*
