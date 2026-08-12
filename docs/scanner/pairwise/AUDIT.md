# Fase 0 — Auditoría: Alpha Scanner + repo referencia pairwise-alpha-strategy

**Fecha:** 2026-08-12  
**QuantLab:** branch `main`, tag restauración `restore/pre-pairwise-integration-20260812`  
**Repo referencia auditado:** [Nisargak18/pairwise-alpha-strategy](https://github.com/Nisargak18/pairwise-alpha-strategy) (Lunor Quest PairWise Alpha Round 3)  
**Alcance:** 22 preguntas obligatorias + implicancias de diseño

---

## Metodología

Inspección directa de código Python/JS, tests y docs en QuantLab. Clon superficial del repo referencia (`strategy.py`, notebooks EDA, README). Sin suposiciones fuera de evidencia.

---

## A. Alpha Scanner actual (QuantLab)

### 1. ¿El Alpha Scanner selecciona únicamente monedas, o también estrategias/parámetros?

**Respuesta:** Selecciona **monedas (instrumentos)** y un **perfil de scoring** (familia de investigación). **No** selecciona estrategias ni hiperparámetros.

**Evidencia:**

- `AlphaScanner.scan()` devuelve `selected: tuple[str, ...]` = top-N `instrument_id`:

```130:199:src/quantlab/research/alpha/__init__.py
    def scan(
        self,
        bars_by_instrument: Mapping[str, Sequence[Bar]],
        *,
        top_n: int = 5,
        min_bars: int = 3,
    ) -> ScannerResult:
        ...
        selected = tuple(s.instrument_id for s in scored[: max(0, top_n)])
        return ScannerResult(
            scores=tuple(scored),
            selected=selected,
            gap_events=tuple(gap_events),
        )
```

- `AlphaScanRequest` incluye `profile` pero no `strategy_id` ni grid de params:

```54:71:src/quantlab/research/alpha/models.py
class AlphaScanRequest:
    venue: str = "lab"
    profile: str = PROFILE_LEGACY_V1
    top_n: int = 5
    run_backtest: bool = False
```

- Pipeline Binance recibe `strategy_id` y `params` **por separado** del scan (`run_binance_lab_pipeline`, L1779–1792 `lab_services.py`).

**Implicancia:** Los detectores pairwise deben emitir **candidatos de par/relación**, no mezclar Sharpe de backtest en el score del scanner.

---

### 2. ¿Dónde y en qué formato se almacenan hoy los resultados de cada señal individual?

**Respuesta:** No hay almacenamiento de **señales de trading** (buy/sell). Se persisten **rankings/scores** de scan.

| Destino | Formato | Contenido |
|---------|---------|-----------|
| `ScanStore` | JSON `{meta, result\|rows, extra}` | Scores, candidatos, hashes reproducibilidad |
| Respuesta API | dict in-memory | Payload scan para UI |
| Reports backtest | `session/reports/<id>/summary.json` | Métricas post-scan (fuera del scanner) |

**Evidencia:**

```102:140:src/quantlab/research/alpha/persist.py
class ScanStore:
    """Almacenamiento JSON local de resultados de scan (session/lab)."""
    def save_alpha_result(...) -> PersistedScanMeta:
        doc = {"meta": meta, "result": payload, "extra": dict(extra or {})}
        path = self._path(result.scan_id)
        path.write_text(_stable_json(doc), encoding="utf-8")
```

**Implicancia:** Nuevo contrato `AlphaSignal` debe persistirse en el mismo `ScanStore` (campo `signals`) o subdirectorio `experiments/alpha_scans/{scan_id}/signals.jsonl`.

---

### 3. ¿Cómo está estructurado el registro de detectores? ¿Plugin/registro o hardcoded?

**Respuesta:** **Hardcoded.** Perfiles en `profiles.py` + `FeatureCalculator` + `CompositeScorer`. Sin registry de detectores.

**Evidencia:**

- `build_profile(name)` — cadena if/elif por nombre (`profiles.py` L135+).
- `FAMILY_SCORING_ALIAS` mapea rama UI → perfil interno (L49–61).
- Búsqueda en `research/alpha/`: **0 matches** para `register|plugin|detector|registry`.
- Contraste: brokers sí tienen `BrokerRegistry` (`brokers/registry.py`).

**Implicancia:** Introducir `DetectorRegistry` en `research/alpha/detectors/` sin romper `build_profile()` — adaptadores legacy, no reemplazo.

---

### 4. ¿Qué contrato de salida usa hoy cada señal?

**Respuesta:** El scanner emite **ranking de activos**, no señales temporales.

**Legacy v1 — `AssetScore`:**

```24:34:src/quantlab/research/alpha/__init__.py
class AssetScore:
    instrument_id: str
    volatility: float
    volume_score: float
    liquidity_score: float
    composite: float
    volatility_n: float = 0.0
    volume_n: float = 0.0
    liquidity_n: float = 0.0
```

**v2 — `RankedCandidate` / `ScoredRow`:**

```114:129:src/quantlab/research/alpha/models.py
class RankedCandidate:
    rank: int
    venue: str
    symbol: str
    composite: float
    base_score: float
    components: tuple[FeatureComponent, ...]
    data_quality: dict[str, Any] | None = None
```

**Señales de estrategia (backtester, no scanner):** `ClassicBarStrategy` → `int` vía `_SIGNAL_TABLE` → `OrderIntent`.

**Implicancia:** Nuevo contrato debe ser **superset** retrocompatible: `RankedCandidate` para scope=individual; `AlphaSignal` para scope=pair.

---

## B. Backtester

### 5. ¿El backtester soporta estrategias de dos piernas (long una / short otra)?

**Respuesta:** **No de forma real.** Motor multi-activo sincroniza barras; estrategias mayormente long-only; pares = **proxies single-series**.

**Evidencia:**

```1:8:src/quantlab/backtester/bar_based.py
"""Facade Backtester bar-based 5A (Fase 6) — mono y multi-activo sincronizado."""
```

```411:416:src/quantlab/research/strategies/classic_bar.py
    def _sig_cointegration_proxy(self, bar: Bar) -> int:
        # Proxy single-series: mean-revert vs SMA (pares reales = stub).
        return self._sig_zscore(bar)

    def _sig_pairs_lag(self, bar: Bar) -> int:
        """Spread close vs close retrasado N (proxy de pares sin 2ª serie)."""
```

```15:18:src/quantlab/brokers/paper/book.py
    """Libro paper mutable controlado (fail-closed: no short por defecto)."""
    allow_short: bool = False,
```

**Implicancia:** Fase posterior obligatoria: `PairSpreadStrategy` + `PaperBook(allow_short=True)` o motor de spread dedicado.

---

### 6. ¿Puede sincronizar fills, timestamps y costos de dos instrumentos en simultáneo?

**Respuesta:** **Motor sí** (`synchronize_bars_by_timestamp`); **pipeline Alpha→BT no** (un backtest por moneda).

**Evidencia:**

```54:60:src/quantlab/simulation/engine.py
def synchronize_bars_by_timestamp(bars: Sequence[Bar]) -> list[list[Bar]]:
    """Agrupa barras por ``timestamp_close`` (orden estable por instrument_id)."""
```

Pipeline Binance (L1966+ `lab_services.py`): loop `for iid, sym in zip(selected_iids, ...)` → `run_lab_backtest(bars=sym_bars)` mono-instrumento.

**Implicancia:** Evaluación de pares requiere `run_pair_backtest(leg_a, leg_b, hedge_ratio, ...)` con fills alineados por step.

---

### 7. ¿Cómo maneja hoy costos de ejecución? ¿Configurable por instrumento?

**Respuesta:** **Por venue + market_type** (VIP0 presets), no por símbolo.

**Evidencia:** `research/sim/fee_schedules.py` → `get_fee_schedule(venue, market_type)` → `MakerTakerFeeModel`. Sim Compare permite override global maker/taker, no por underlying.

**Implicancia:** Pares deben estimar costo = fee(leg_a) + fee(leg_b) + slippage proxy; usar schedule del venue compartido en v1.

---

## C. Validación

### 8. ¿Existe walk-forward real o solo split fijo 70/30?

**Respuesta:** **Ambos existen; el pipeline Alpha Binance usa split fijo 70/30**, no rolling folds.

**Alpha pipeline:**

```34:88:src/quantlab/research/alpha/walk_forward.py
def split_bars_walk_forward(..., rank_fraction: float = 0.70):
    """Primera fracción → ranking; resto → backtest (sin overlap temporal)."""
    rank_part = seq[:cut]
    bt_part = seq[cut:]
```

**Validation module (rolling):**

```50:71:src/quantlab/validation/splits.py
def walk_forward(bars, *, train_size, test_size, step=None):
    while start + train_size + test_size <= len(bars):
        folds.append(WalkForwardSplit(train=..., test=..., fold=fold))
        start += step
```

**Implicancia:** Walk-forward rolling es **requisito de implementación** para pairwise; conectar `validation/splits.walk_forward` al pipeline de evaluación, no solo al panel Validation sintético.

---

### 9. ¿Hay purging/embargo o riesgo de leakage?

**Respuesta:** **Anti-overlap básico** (`assert_no_future_overlap`); **sin purging ni embargo** (estilo López de Prado).

**Evidencia:**

```74:80:src/quantlab/validation/splits.py
def assert_no_future_overlap(train, test):
    if first_test < last_train:
        raise ValidationError("leakage temporal: test solapa train")
```

Búsqueda `purging|embargo` en `src/quantlab`: **0 resultados**.

Kronos restringido al tramo rank (`kronos/integrate.py`, `lab_services.py` L1942).

**Implicancia:** Implementar `purged_k_fold` o embargo mínimo = max(lookback, holding_period) en evaluación pairwise.

---

### 10. ¿Se registra el historial de todas las pruebas/backtests (trials)?

**Respuesta:** **Parcial — stores fragmentados**, sin conteo global de trials para deflated Sharpe.

| Store | Scope |
|-------|-------|
| `ExperimentRegistry` (SQLite) | Experimentos con metadata |
| `GridSearchOptimizer.history` | Trials de optimizer |
| `ScanStore` | Scans alpha |
| `session/reports/` | Reports individuales |
| `optimizer_runs.py` | Historial optimizer sesión |

**Gap:** Pipeline Binance batch no persiste automáticamente cada BT salvo `reports_dir` explícito. **No hay** `trial_registry` unificado scan→BT→optimize.

**Implicancia:** `TrialLedger` obligatorio antes de Deflated Sharpe — registrar cada (par, lag, ventana, perfil) probado.

---

### 11. ¿Existe Sharpe, Sharpe deflactado o equivalente?

**Respuesta:** **Sharpe sí** (`metrics/engine.py` L44–52). **Deflated Sharpe: no** (0 matches en repo).

```44:52:src/quantlab/metrics/engine.py
def sharpe_ratio(returns, *, periods_per_year: float = 252.0) -> float:
    ...
    return (mean / std) * sqrt(periods_per_year)
```

**Implicancia:** Implementar `deflated_sharpe_ratio()` en `validation/` o `metrics/` con `n_trials` desde `TrialLedger`.

---

## D. Datos

### 12. ¿Qué exchanges/mercados están integrados (Spot, Futures)?

**Respuesta:**

| Venue | Spot | Perpetuals | Fetch MD |
|-------|------|------------|----------|
| binance | ✓ | ✓ | ✓ (scanner default spot USDT) |
| okx | ✓ | ✓ | ✓ |
| bybit | ✓ | ✓ | ✓ |
| hyperliquid | ✗ | ✓ | ✓ |
| a3 | ✗ | futuros granos | ✓ |
| lab | sintético | ✗ | ✓ |

**Evidencia:** `research/alpha/venues.py` L58–134.

Pipeline default: Binance Spot USDT (`market_type="spot"`, `lab_services.py` L1846).

---

### 13. ¿Los datos alcanzan para correlación rezagada y cointegración con significancia?

**Respuesta:** **Infraestructura sí; defaults del scanner no.**

- Scanner API default: `kline_limit=24` — **insuficiente** para ADF/Johansen o lag estable.
- Límite lab: hasta **525,600** velas vía `period_days` en Sim/MC (`md_limits`).
- Estrategias stats: proxies single-asset (`strategy_catalog.py` L246–252).

**Implicancia:** Detectores pairwise deben exigir `min_bars` configurable (ej. 500+ para 1h, 2000+ para cointegración) y rechazar con `insufficient_history`.

---

### 14. ¿Pares candidatos: mismo exchange/mercado o cruzar fuentes?

**Respuesta:** **Ranking cross-venue sí** (`scan_multi_venue`); **backtest de spread sincronizado cross-venue no**.

**Evidencia:** `venues.py` `scan_multi_venue()` combina barras elegibles. Sim Compare acepta pares `{venue, underlying}` pero backtestea **cada uno por separado** (`compare.py` L144–163).

**Implicancia v1:** Restringir pares a **mismo venue + market_type + timeframe** (decisión producto — ver DESIGN.md defaults).

---

## E. Repo referencia: pairwise-alpha-strategy (preguntas 15–22)

**Nota:** Repo clonado en `/tmp/pairwise-audit`. Es submission Lunor Quest R3; **no** es el mismo que QuantLab. Código principal: `strategy.py` (~38 líneas) + notebooks EDA.

### 15. ¿Qué problema resuelve? ¿Supuestos de mercado?

**Respuesta:** Generar señales BUY/SELL/HOLD para **SOL** usando retornos relativos vs **BTC y ETH** como anchors. Supone:

- Mercado crypto altamente correlacionado.
- Alpha = desviación de SOL vs basket 50/50 BTC+ETH.
- Reglas determinísticas, sin ML.
- Datos Binance OHLCV 1H (ETH resampleado desde 4H).

**Evidencia:** `README.md` L7–37, `strategy.py` L3–10.

---

### 16. ¿Trabaja sobre precios o retornos?

**Respuesta:** **Retornos** (`pct_change`) para la señal alpha; precios para merge y rolling features.

```17:31:strategy.py (referencia)
    df["ret_target"] = df["Close"].pct_change()
    df["ret_BTC"] = df["close_BTC_1h"].pct_change()
    df["ret_ETH"] = df["close_ETH_4h"].pct_change(fill_method=None)
    df["alpha"] = df["ret_target"] - 0.5 * (df["ret_BTC"] + df["ret_ETH"])
```

---

### 17. ¿Cómo calcula lags? ¿Cómo mide cointegración?

**Respuesta:**

- **Lags:** `shift(1)`, `pct_change(periods=1|2)` sobre target — **no** búsqueda sistemática de lag óptimo ni significancia.
- **Cointegración:** **No implementada.** Notebook EDA usa spread de retornos + z-score rolling 48h, no ADF/Johansen ni hedge ratio OLS/Kalman.

**Evidencia:** `strategy.py` L15–19; notebook `spread_z = (spread - rolling(48).mean()) / rolling(48).std()`.

---

### 18. ¿Cómo selecciona pares? ¿Filtros?

**Respuesta:** **Par fijo** SOL vs {BTC, ETH}. Sin universo dinámico ni filtros de liquidez/correlación mínima en `strategy.py`.

---

### 19. ¿Cómo valida fuera de muestra? ¿Corrige múltiples comparaciones?

**Respuesta:** **No.** Notebook calcula Sharpe in-sample sobre toda la serie (`Sharpe: -0.38, MaxDD: -96.73%`). Sin split train/test, sin Bonferroni/BH, sin walk-forward.

---

### 20. ¿Incorpora costos de transacción?

**Respuesta:** **No** en `strategy.py` ni en el backtest del notebook (equity = cumprod de retorno × position, sin fees).

---

### 21. ¿Tiene leakage?

**Respuesta:** **Sí, riesgo alto.**

- Umbrales fijos (`alpha > 0.002`) sin calibración OOS separada.
- Z-score rolling 48h + señales en **mismo período** que métricas Sharpe.
- `spread_z_lag1 = shift(1)` mitiga lookahead de 1 bar pero **no** separación train/validation.

---

### 22. Componentes: adaptables / reescritura / descartar

| Componente | Veredicto | Motivo |
|------------|-----------|--------|
| Concepto anchor + target | **Adaptable** | Encaja como detector `relative_return_alpha` |
| Fórmula alpha retornos | **Adaptable** | Una señal más, normalizada transversalmente |
| Merge temporal por timestamp | **Adaptable** | QuantLab ya tiene `synchronize_bars_by_timestamp` |
| Lag shift(1/2) ad hoc | **Reescritura** | Reemplazar por búsqueda multi-lag + corrección BH |
| Umbrales fijos 0.002 | **Descartar** | Sin OOS ni corrección múltiple |
| Spread z-score notebook | **Reescritura** | Integrar en `pair_spread.py` con estabilidad rolling |
| Sharpe in-sample como KPI | **Descartar** | Causa raíz del sobreajuste actual |
| Clase `PairwiseAlphaStrategy` | **Descartar** | Referenciada en test pero **no existe** (`src/utils.py` vacío) |
| Cointegración ADF/Johansen | **N/A** | Implementar desde cero en QuantLab |

---

## F. Decisiones de producto pendientes (solo el usuario)

Estas **no** se resuelven por auditoría. El diseño propone **defaults operativos** para avanzar en paralelo (ver `DESIGN.md` §0):

| # | Pregunta | Default propuesto (implementación v1) |
|---|----------|----------------------------------------|
| P1 | ¿Spot, Futures o ambos? | **Spot primero** (scanner ya default Binance spot); Futures en fase 2 |
| P2 | ¿Mismo exchange o cross-venue? | **Mismo venue + market_type** (Binance spot USDT) |
| P3 | ¿Prioridad lag vs cointegración? | **Lagged correlation primero** (menor costo computacional) |
| P4 | ¿Señales para monedas, estrategias o ambas? | **Pares/mercados candidatos**; estrategia compatible se elige en paso Simulador separado |

---

## G. Implicancias para el diseño (síntesis)

1. **No mezclar selección y evaluación:** Scanner emite `AlphaSignal` candidatas; Sharpe/DSR solo en `validation.py` post-backtest.
2. **Registry de detectores:** Nuevo módulo; perfiles legacy = adaptadores, no rewrite.
3. **Contrato superset:** `AlphaSignal` + migración gradual de `RankedCandidate` (scope=individual).
4. **TrialLedger obligatorio:** Sin conteo honesto de trials no hay Deflated Sharpe.
5. **Walk-forward rolling:** Requisito nuevo; split 70/30 actual insuficiente.
6. **Purging/embargo:** Implementar en evaluación pairwise (lookback + holding).
7. **Backtester par:** Extensión necesaria; proxies actuales no sirven para validación seria.
8. **Min bars elevados:** Defaults scanner (24) incompatibles con stats pairwise — gate explícito.
9. **Repo referencia:** Solo ideas conceptuales; **no copiar** thresholds ni validación.
10. **Research only:** Salida = candidatos + OrderIntent en paper; `LIVE_BLOCKED=True` intacto.

---

## H. Evidencia adicional consultada

| Archivo | Relevancia |
|---------|------------|
| `src/quantlab/workbench/lab_services.py` | Pipeline scan+BT |
| `src/quantlab/research/alpha/profiles.py` | Perfiles hardcoded |
| `src/quantlab/research/alpha/scoring.py` | Normalización min-max |
| `src/quantlab/research/alpha/persist.py` | Persistencia JSON |
| `src/quantlab/validation/leakage.py` | Checks leakage básicos |
| `src/quantlab/optimizer/grid.py` | Historial trials optimizer |
| `src/quantlab/experiments/registry.py` | SQLite experimentos |
| `src/quantlab/workbench/strategy_catalog.py` | Stubs cointegration_proxy |

---

*Fase 0 completada. Siguiente entregable: `DESIGN.md`.*
