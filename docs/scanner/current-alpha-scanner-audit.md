# Auditoría Alpha Scanner actual — FASE 0 (baseline)

**Fecha:** 2026-07-27  
**Versión tip repo:** 1.01.0  
**Alcance:** discovery / baseline — **sin cambio de lógica de scoring**  
**Baseline controlado:** [`fase0_baseline_synthetic.json`](fase0_baseline_synthetic.json)

---

## 1. Arquitectura actual

```
UI (scanner.js | guided_lab.js | chat tools)
        │
        ▼
HTTP API (server.py → api.py)
        │
        ▼
lab_services.py
   ├─ run_lab_scanner()           → universo sintético WB:A/B/C
   ├─ run_binance_lab_scanner()   → list_spot_symbols + klines → AlphaScanner
   └─ run_binance_lab_pipeline()  → scan → backtest top-N
        │
        ▼
research/alpha/__init__.py  (AlphaScanner)
research/alpha/explain.py   (contribución = peso × normalizado)
```

No existe un paquete `alpha_scanner/` separado. El núcleo es `quantlab.research.alpha`.

El Alpha Scanner **no envía órdenes**. Binance MD es público read-only. LIVE_BLOCKED se mantiene.

---

## 2. Archivos involucrados

| Área | Path |
|------|------|
| Núcleo | `src/quantlab/research/alpha/__init__.py` |
| Explain | `src/quantlab/research/alpha/explain.py` |
| Lab adapters | `src/quantlab/workbench/lab_services.py` |
| MD Binance | `src/quantlab/brokers/binance/public_md.py` |
| API | `src/quantlab/workbench/api.py`, `server.py`, `api_catalog.py` |
| UI Guided | `src/quantlab/workbench/static/js/panes/guided_lab.js` |
| UI panel | `src/quantlab/workbench/static/js/panes/scanner.js` |
| Chat | `src/quantlab/workbench/chat/tools.py` |
| Slice F4 | `src/quantlab/vertical_slice/fase4.py` |
| Demo | `playground/scan_demo.py` |
| Tests | `tests/unit/research/test_alpha_*.py`, `test_binance_lab_f111.py`, nightly TD-06/TD-11 |
| Docs | `docs/FASE_111_BINANCE_ALPHA_PIPELINE.md`, DEC-047, TD-06/TD-11 |

---

## 3. Fórmula actual (exacta)

**Pesos default** (`ScannerWeights`):

| Factor | Peso |
|--------|------|
| volatility | 0.35 |
| volume | 0.35 |
| liquidity | 0.30 |

**Por instrumento** (tras `align_bars_for_gaps`, default `FORWARD_FILL`):

1. Filtrar barras live `volume > 0` (TD-11); si ninguna, usa todas.
2. `volatility` = `pstdev` de retornos simples \((c_i - c_{i-1})/c_{i-1}\); si &lt;2 retornos → 0.
3. `volume_score` = media de volúmenes.
4. `liquidity_score` = \(1 / (\overline{(H-L)/C} + 10^{-9})\).

**Normalización:** min-max **cross-sectional** sobre el universo elegible (`min_bars`):

\[
n(x)=\begin{cases}0 & \max=\min\\ (x-\min)/(\max-\min) & \text{si no}\end{cases}
\]

**Composite:**

\[
\text{composite} = 0.35\,n(\text{vol}) + 0.35\,n(\text{volume}) + 0.30\,n(\text{liquidity})
\]

Redondeo a 8 decimales. Orden: `(-composite, instrument_id)`.  
`selected` = primeros `top_n`.

**Explain (TD-06):** `contrib = weight * normalized`; `contrib_sum ≈ composite`.

---

## 4. Fuentes de datos

### Lab sintético

- `make_scanner_universe()`: `WB:A`, `WB:B`, `WB:C` — 16 barras 1m deterministas (2024-06-01 UTC).
- Sin red. Reproducible.

### Binance

1. `list_spot_symbols(quote=USDT, limit=symbol_limit)` — primeros N `TRADING` del `exchangeInfo` (**orden API, no por volumen**).
2. `fetch_universe_bars` — klines `interval` × `kline_limit` (8–3000, paginado).
3. Errores de kline por símbolo: **omitidos en silencio**.
4. Ventana = **últimas N velas hasta “ahora”** (sin `as_of` / startTime fijo).

`POST /api/lab/binance/scan` lista símbolos + book: **no** es AlphaScanner.

---

## 5. Origen de `fetched` / `top`

| Campo UI/API | Origen |
|--------------|--------|
| `top` / `top_n` | Request (default 3 sintético / 5 Binance); UI Guided Lab fija 5 |
| `selected` | IDs internos (`WB:*` o `BN:*`) |
| `selected_symbols` | Solo Binance: símbolos crudos |
| `n_symbols_fetched` | `len(bars_by_symbol)` tras fetch (≤ symbol_limit) |
| **`fetched`** | **No existe en JSON**; la UI imprime `fetched=` usando `n_symbols_fetched` |

---

## 6. Baseline controlado (ejecutado 2026-07-27)

Universo sintético WB — `run_lab_scanner(top_n=3)`:

| Rank | Instrumento | Composite |
|------|-------------|-----------|
| 1 | WB:B | 0.35 |
| 2 | WB:C | 0.30 |
| 3 | WB:A | 0.12617251 |

Detalle en `docs/scanner/fase0_baseline_synthetic.json`.

---

## 7. Resultados de pruebas iniciales (FASE 0)

Ejecutado en repo tip:

```text
pytest tests/unit/research/test_alpha_scanner.py \
       tests/unit/research/test_alpha_explain.py \
       tests/unit/workbench/test_binance_lab_f111.py \
       tests/unit/workbench/test_lab_api.py
→ 27 passed

ruff check src/quantlab/research/alpha src/quantlab/workbench/lab_services.py
→ All checks passed

mypy --strict src/quantlab/research/alpha
→ Success: no issues found in 2 source files
```

Suite completa del repo: **no re-ejecutada en esta fase** (costo alto); subset alpha/F111 PASS.

---

## 8. Limitaciones

1. Solo 3 factores (vol / volumen / liquidez proxy por rango OHLC).
2. Sin perfiles por estrategia (momentum vs MM vs funding).
3. Sin filtros de elegibilidad tipados (exclusiones silenciosas en Binance).
4. Sin quality report (freshness / completeness / stale).
5. Sin penalizaciones explícitas.
6. Normalización min-max frágil a outliers y a universo de 1 elemento (todos n=0).
7. Sin persistencia de scans (solo `last_lab_result` en RAM).
8. Sin multi-venue (Hyperliquid / Bybit / OKX no cableados al scanner).
9. Sin `as_of_time` → ranking Binance no reproducible entre corridas.
10. Pipeline: **misma ventana** para ranking y backtest → selección in-sample.
11. Universo Binance truncado por orden de `exchangeInfo`, no por liquidez.
12. Panel `scanner.js` solo sintético; Binance alpha vive en Guided Lab / API / chat.
13. Docs `Arquitectura.md` §6.8 desfasados (`get_opportunities` no implementado).

---

## 9. Riesgos

| Riesgo | Severidad | Nota |
|--------|-----------|------|
| Look-ahead / selección in-sample en pipeline | Alta | Rank y BT sobre mismas últimas N klines |
| Ventana anclada a “ahora” | Alta | No hay punto-en-tiempo |
| Kline incompleta (vela abierta) | Media | Features del presente parcialmente anticipadas |
| Datos faltantes → 0 en vol | Media | &lt;2 retornos ⇒ volatility=0 (no null) |
| Gaps FF con volume=0 | Baja (mitigado TD-11) | Vol/liq usan solo live |
| Comparar venues futuros sin normalizar unidades | Alta (futuro) | No implementar sin grupos comparables |
| Score ≠ rentabilidad | Producto | Debe quedar explícito en UX |

---

## 10. Casos no cubiertos

- L2 / profundidad / libro cruzado.
- Funding / OI / basis.
- Mean-reversion / MM / Avellaneda profiles.
- Exclusión por mercado nuevo, spread, stale.
- `missing_factor_policy` (hoy no hay factores opcionales tipados).
- Multi-venue ranking.
- Comparar / repetir scans versionados.
- Cancelación / progreso / rate-limit observability del scan.
- Holdout temporal (scan en T−Δ, backtest en (T−Δ, T]).

---

## 11. Tratamiento de ausencias / ceros (hallazgos)

| Situación | Comportamiento actual |
|-----------|------------------------|
| &lt;2 retornos | `volatility = 0.0` (no null) |
| Volumen vacío | `volume_score = 0.0` |
| Rango OHLC vacío | `avg_range = 1.0` → liquidez finita |
| Kline Binance falla | Símbolo **omitido** (sin exclusion_reason) |
| Min-max degenerado | `n(*) = 0` |
| Forward-fill gap | OHLC plano, `volume=0` |

**Violación conceptual vs objetivo:** “ausencia ≠ cero” — hoy varios caminos usan cero.

---

## 12. Propuesta de migración compatible

**Principio:** evolucionar `AlphaScanner` / adapters; **no** crear un segundo scanner desconectado.

### Fases siguientes (bajo riesgo primero)

| Fase | Entrega | Compatibilidad |
|------|---------|----------------|
| 1 | Modelos tipados `AlphaScanRequest/Result` + wrappers | `AlphaScanner.scan` sigue; API antigua delega |
| 2 | UniverseBuilder + EligibilityFilter + DataQualityReport | Binance path emite exclusiones explícitas |
| 3 | FeatureCalculator modular (mantiene 3 factores v1 como profile `balanced_legacy`) | Misma fórmula si profile=`legacy_v1` |
| 4 | Normalizer robusto + PenaltyEngine + ExplanationBuilder | Opt-in; default puede ser legacy |
| 5 | Profiles versionados | Presets Guided Lab |
| 6 | Multi-venue adapters (HL/Bybit/OKX) detrás de contrato MD | Capability flags |
| 7 | Persistencia scan_id / hashes / compare | Session dir `scans/` |
| 8 | UX Guided: básico/avanzado, “¿Por qué?”, exclusiones | Badges HISTÓRICO/SINTÉTICO ya iniciados |
| 9 | Perf / observability | Sin romper tests |
| 10 | Docs + informe final | — |

### Compatibilidad binaria / API

- Mantener `POST /api/lab/scanner` y `/api/lab/binance/scanner`.
- Añadir campos opcionales en response (`exclusions`, `data_quality`, `scanner_version`).
- Profile default inicial: `legacy_v1` ≡ fórmula actual (pesos 0.35/0.35/0.30, min-max).
- Tests golden: `fase0_baseline_synthetic.json` debe seguir reproducible con `legacy_v1`.

### No hacer sin aprobación

- Romper response shape sin versión.
- Eliminar `AlphaScanner` actual.
- Wiring de ejecución / credenciales trading.
- Afirmar que el nuevo ranking es “más rentable”.

---

## 13. Decisiones FASE 0

1. Baseline sintético fijado y versionado en docs.
2. Migración incremental sobre `research/alpha` + `lab_services`.
3. Prioridad cuantitativa: point-in-time + exclusiones tipadas + ausencia≠cero antes que multi-venue UI.
4. Commits: solo con pedido explícito del usuario (regla de repo).

---

## 14. Próximo paso inmediato (FASE 1)

Implementar contratos tipados y adapter de compatibilidad **sin cambiar scores default**, con tests que fijen el baseline sintético de esta auditoría.
