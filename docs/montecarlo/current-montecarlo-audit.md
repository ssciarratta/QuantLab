# Auditoría Monte Carlo — estado actual (FASE 0)

**Fecha:** 2026-07-27  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** `True` (verificado en runtime y tests)  
**Método:** inspección de código + baseline ejecutado; **sin inventar** comportamiento no presente en el repo.

---

## 1. Arquitectura (as-is)

```
UI (montecarlo.js)
  → POST /api/lab/montecarlo  (api.handle_post_lab_montecarlo)
    → lab_services.run_lab_montecarlo
         ├─ make_synthetic_bars(n_bars)     # 1m, instrument WB:SYN
         ├─ runner = BarBacktester + BuyOnceStrategy(qty=1)
         └─ MonteCarloSimulator(seed=42).run(bars, runner, …)
              ├─ por escenario: _perturb(OHLC) → re-ejecuta runner
              └─ agrega final_equities → mean/std/CI
    → persist_montecarlo_run → session/montecarlo/<run_id>/summary.json
GET /api/lab/montecarlo/history[+/{run_id}]
```

No hay cableado Scan → Instrument → Backtest → Monte Carlo. El lab MC es un **mini demo aislado** (barras sintéticas + estrategia hardcodeada).

---

## 2. Archivos clave

| Rol | Path |
|-----|------|
| Motor MC | `src/quantlab/montecarlo/simulator.py` |
| Export paquete | `src/quantlab/montecarlo/__init__.py` |
| Orquestación lab | `src/quantlab/workbench/lab_services.py` → `run_lab_montecarlo` |
| Persistencia | `src/quantlab/workbench/montecarlo_runs.py` (`MONTECARLO_SCHEMA_VERSION = 1`) |
| API | `src/quantlab/workbench/api.py` (`handle_post/get_lab_montecarlo*`) |
| Rutas HTTP | `src/quantlab/workbench/server.py` |
| UI | `src/quantlab/workbench/static/js/panes/montecarlo.js` |
| Cliente API | `src/quantlab/workbench/static/js/api.js` |
| Sesión dir | `src/quantlab/workbench/session.py` → `montecarlo_dir` |
| Backtester usado | `src/quantlab/backtester/bar_based.py` |
| Estrategia lab | `quantlab.research.strategies.buy_once.BuyOnceStrategy` |
| Barras demo | `make_synthetic_bars` en `lab_services.py` (timeframe `"1m"`) |

Docs dedicadas `docs/montecarlo/*`: **no existían** antes de esta auditoría.

---

## 3. Método real (código)

### 3.1 Qué se simula

1. Se generan `n_bars` velas **sintéticas** 1m (`WB:SYN`, precio base 100, drift +1 por barra).
2. Por cada escenario `i = 1..n_scenarios`:
   - Se **perturban OHLC** de todas las barras (mismo factor por barra).
   - Se **re-ejecuta** `BarBacktester` + `BuyOnceStrategy({"quantity": "1"})` con `initial_cash=50000` y fee Spot Binance VIP0.
3. De cada `SimulationResult` se toma **solo** `equity_curve[-1].equity` → `final_equities`.
4. Se calculan `mean_equity`, `std_equity`, `ci_low`, `ci_high`.

**No** se usan trades/L2. **No** se lee un backtest ni scan previo. **No** hay bootstrap de retornos ni block bootstrap (aunque el schema futuro podría contemplarlo).

### 3.2 Perturbación (`_perturb`)

```python
shock = 1 + rng.gauss(0, noise_bps / 10000.0)
# si shock <= 0 → clamp a 0.0001
open/high/low/close *= shock   # mismo shock por barra
volume sin cambio
```

- Distribución: **gaussiana** (`random.Random.gauss`).
- `noise_bps=10` ⇒ σ = 10/10000 = **0.001** = **0.10%** por barra (independiente).
- OHLC de la misma barra reciben el **mismo** multiplicador; barras distintas, shocks independientes.
- Timestamps / timeframe / instrument_id se preservan.

### 3.3 ¿Cada escenario re-ejecuta la estrategia?

**Sí.** El `runner` recibe la secuencia de barras ruidosas y corre el backtester completo. El motor guarda `results: tuple[SimulationResult, …]` en memoria, pero el **payload lab / summary.json no persiste trayectorias** — solo `final_equities` y agregados.

### 3.4 Determinismo / seed

- `MonteCarloSimulator(seed=…)` fija `random.Random(self._seed)`.
- Lab hardcodea `seed=42` (API no expone seed editable hoy).
- Baseline: dos corridas `n_scenarios=5, n_bars=16, noise_bps=10` → `final_equities` **idénticos** (`repro True`).

### 3.5 Look-ahead

En el path actual no hay features forward-looking explícitas ni `as_of_time`. El riesgo de look-ahead futuro aparece si se enchufa MC a datasets/features reales sin reloj de simulación — **fuera del código actual**.

---

## 4. Significado exacto de parámetros

| Campo | Qué es en código | Default lab | Rango lab |
|-------|------------------|-------------|-----------|
| `n_scenarios` | Cantidad de re-ejecuciones con barras perturbadas | 5 | 2–20 (“mini”) |
| `n_bars` | **Cantidad de velas sintéticas 1m** generadas para el experimento (no “largo de trayectoria MC” abstracto; no barras de un BT previo) | 16 | 8–60 |
| `noise_bps` | Desvío estándar del shock multiplicativo gaussiano en **basis points** (÷10000) | 10.0 | sin validación de rango en API (solo tipo numérico) |
| `seed` | Semilla de `random.Random` del simulador | 42 (fijo) | no configurable vía API lab |
| `ci` / `ci_level` | Nivel nominal del intervalo; motor usa `ci=0.95` → z=1.96; otro valor ≈ z=1.64 | 0.95 | binario 0.95 vs resto |
| `mean_equity` | Media aritmética de `final_equities` | — | — |
| `std_equity` | `statistics.pstdev(finals)` (**población**, no muestral) | — | — |
| `ci_low` / `ci_high` | Ver §5 | — | — |
| `final_equities` | Equity final por escenario | — | — |

### Clarificación de “Bars” (para UI futura)

- Label preciso: **Barras del dataset sintético (1m)** o **Horizonte de velas 1m**.
- Duración equivalente actual: `n_bars × 1 minuto` (p.ej. 16 barras ≈ 16 minutos).
- **No** confundir con número de escenarios ni con longitud de path de precios futuros.

---

## 5. Fórmula CI95 (real)

```
mu    = mean(final_equities)
sigma = pstdev(final_equities)          # población
z     = 1.96 si ci≈0.95 else 1.64
half  = z * sigma / sqrt(N)
ci_low, ci_high = mu - half, mu + half
```

**Interpretación correcta:** intervalo de confianza **Wald / normal approx para la media** de equities finales, no percentiles de la distribución de escenarios (no es un “CI del resultado” tipo P2.5–P97.5).

Con N pequeño (lab max 20) el IC de la media es estrecho aunque la dispersión de escenarios importe más al usuario — limitación estadística documentada.

---

## 6. Baseline ejecutado (2026-07-27)

```
n_scenarios=5, n_bars=16, noise_bps=10.0, seed=42, persist=False
mean_equity ≈ 50013.90115
std_equity  ≈ 0.17463
ci_low      ≈ 50013.74808
ci_high     ≈ 50014.05422
final_equities ≈ [50013.80, 50013.70, 50014.22, 50013.90, 50013.89]
reproducible: True
payload keys: ci_*, final_equities, kind, live_*, mean/std_equity, n_bars,
              n_scenarios, noise_bps, ok, path, persisted, run_id, seed
```

**Ausente en payload:** strategy_id, venue, symbol, timeframe, dataset_*, backtest_id, scan_id, initial_equity explícito, fee model id, code_commit, trayectorias, drawdown, método nombrado, distribution label.

---

## 7. Persistencia y schema

- `schema_version = 1` en `montecarlo_runs.MONTECARLO_SCHEMA_VERSION`.
- Archivo: `montecarlo/<run_id>/summary.json` (atomic write).
- Lista: hasta 100 corridas; columnas: run_id, created_at, n_scenarios, n_bars, seed, mean/std, ci_*.
- Sin FK a backtest/scan/dataset. Sin hashes de config/código.
- Lectura fail-closed de `run_id` (charset + path traversal).

---

## 8. UI actual

- Labels ambiguos: **N**, **bars**.
- Muestra mean/std/CI95, seed, n_bars, run_id, raw JSON completo.
- Historial mínimo (run_id, n, mean, CI).
- Sin cabecera de contexto, sin tooltips bps, sin gráficos, sin abrir BT/scan.

---

## 9. Limitaciones y riesgos

| # | Limitación / riesgo |
|---|---------------------|
| L1 | Demo aislado: no traza Scan→BT→MC |
| L2 | Estrategia/instrumento/capital fijos en lab |
| L3 | Solo equities finales persistidos; sin drawdown de trayectorias en summary |
| L4 | CI = IC de la **media**, fácil de malinterpretar como rango de outcomes |
| L5 | `pstdev` poblacional + N chico |
| L6 | Shock i.i.d. por barra; no preserva autocorrelación / vol clustering |
| L7 | Seed no expuesto en API lab |
| L8 | Cap “mini” 20 escenarios — poco para cuantiles estables |
| L9 | Sin `as_of_time` / anti look-ahead en contrato |
| L10 | Históricos schema v1 sin contexto: migración debe ser no destructiva |

---

## 10. Tests existentes (baseline)

| Suite | Resultado FASE 0 |
|-------|------------------|
| `test_f11_montecarlo` | PASS |
| `tests/unit/workbench/test_mc_export_f34.py` | PASS |
| `test_lab_montecarlo` | PASS |
| **Total MC-related** | **11 passed** |

Gates:

- `ruff check` `src/quantlab/montecarlo` + `montecarlo_runs.py`: **All checks passed**
- `mypy --strict src/quantlab/montecarlo`: **Success**

---

## 11. Plan de migración (Fases 1–12)

| Fase | Objetivo | Principio |
|------|----------|-----------|
| 1 | Modelos `MonteCarloExperimentContext`, `MonteCarloConfig`, result enriquecido | Evolucionar `simulator.py` + tipos; no módulo paralelo |
| 2 | Persistencia relaciones + hashes + schema_version bump compat | Extender `montecarlo_runs.py` |
| 3 | Compat lectura v1 → “No disponible” | Fallbacks null, nunca 0 sentinel |
| 4 | Métricas backend honestas (solo si datos) | Sin inventar drawdown sin paths |
| 5–9 | UI cabecera / qué simulamos / resultados / gráficos / historial | Vanilla JS |
| 10 | Navegación Scan/BT/MC | Wire IDs si existen |
| 11 | Tests exhaustivos | TDD donde crítico |
| 12 | Docs guía + interpretación + trazabilidad + UX audit | `docs/montecarlo/*` |

**Prioridad:** corrección estadística > trazabilidad > reproducibilidad > claridad > compat > utilidad > perf.

**No romper:** summaries `schema_version: 1` existentes; `LIVE_BLOCKED`; API paths actuales.

---

## 12. Decisiones de auditoría (congeladas)

1. **Método implementado único:** perturbación gaussiana multiplicativa de OHLC + re-backtest (“price shock re-run”).
2. **`n_bars`:** longitud del dataset de velas de entrada (hoy sintéticas 1m), no un hiperparámetro abstracto de “pasos MC”.
3. **`noise_bps`:** σ del gauss en bps sobre precio (÷10000).
4. **CI95:** IC de la media de equities finales (Wald), no percentiles de escenarios.
5. **Trayectorias:** disponibles en objeto Python `MonteCarloResult.results`, **no** en JSON persistido hoy → métricas de path requieren Fase 4 consciente de memoria.
