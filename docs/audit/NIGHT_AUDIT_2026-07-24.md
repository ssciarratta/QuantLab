# 🛡️ CERTIFICADO — AUDITORÍA NOCTURNA INTEGRAL

- **Estado**: 🟢 VALIDADO (suite completa en verde tras correcciones zero-doubt)
- **Fecha**: 2026-07-24 (noche)
- **Alcance**: Proyecto íntegro `src/quantlab` + tests unitarios/integración
- **Modo**: Autoevaluación autónoma — correcciones **solo** sin duda

---

## 🧪 Calidad final

| Check | Resultado |
|-------|-----------|
| `uv run pytest` | **PASSED** (141 tests) |
| `uv run mypy --strict src/quantlab` | **PASSED** |
| `uv run ruff check src/quantlab` | **PASSED** |
| Coverage (`src/quantlab`) | **~88%** (≥80 requerido) |

Suite nueva de regresiones: `tests/unit/nightly/test_night_audit_regressions.py`  
Smoke F4: `tests/unit/vertical_slice/test_fase4_smoke.py`

---

## ✅ Encontrado y corregido (zero-doubt)

| ID | Defecto | Fix |
|----|---------|-----|
| N1 | `require_positive` / `require_non_negative` aceptaban `Infinity`/`NaN` | Rechazo explícito |
| N2 | Fill de instrumento distinto a la barra | `instrument_mismatch` en fill model |
| N3 | `Order.price` LIMIT = precio post-slippage | LIMIT conserva `intent.price` |
| N4 | Latencia: estrategia veía portfolio pre-fill | Due fills **antes** de `StrategyContext` |
| N5 | `apply_fill` aceptaba qty/precio ≤ 0 | `ValueError` defensivo |
| N6 | `Fill.fee.fill_id` podía no coincidir | Invariante en `Fill.__post_init__` |
| N7 | `Order` FILLED con `filled_quantity` incompleta | Invariante status↔cantidad |
| N8 | FeatureStore path `..` / `.` | `_safe_segment` rechaza segmentos inseguros |
| N9 | FeatureStore write no atómica | `atomic_write_*` en `put` |
| N10 | Serialización features omitía points no-dict | `ValidationError` explícito |
| N11 | Validators/trades multi-instrumento falsos OOO | Estado **por** `instrument_id` |
| N12 | `build_bars_from_trades` mezclaba instrumentos | `A3DataError` si trade ajeno |
| N13 | Slippage bps ≥ 10000 → SELL ≤ 0 | Rechazo en `__post_init__` |
| N14 | `min_delay` documentado pero no implementado | Rechazo honesto hasta implementación |
| N15 | Causal permitía `timestamp_close` iguales | Orden **estrictamente** ascendente |
| N16 | Alpha FORWARD_FILL inflaba liquidez (rango 0) | Score liquidez ignora `volume==0` |

---

## ⚠️ Encontrado y NO corregido (duda / deuda / fuera de alcance)

| ID | Ítem | Por qué no se tocó |
|----|------|---------------------|
| R1 | Colisión path FeatureStore (`a/b` vs `a_b`) | Requiere hashing de segmentos (breaking paths) |
| R2 | `verify_dataset` no recalcula hash del storage | Contrato MVP vs integridad fuerte — decisión de producto |
| R3 | ATR nombrado vs Wilder real | RSI es Wilder; ATR es SMA de TR — posible naming |
| R4 | Sortino `/N` vs Sharpe `/(N-1)` | Convención; no hay spec única |
| R5 | Calmar anualiza por #puntos, no calendario | Aceptable en MVP bar-based |
| R6 | `profit_factor=999.0` sentinel | Distorsiona rankings si se trata como ratio real |
| R7 | Fees no entran en `realized_pnl` bruto | Contabilidad intencional a confirmar |
| R8 | LIMIT GTC no resta entre barras | Alineado a DEC-045 same-bar baseline |
| R9 | `freeze_mapping` superficial (nested mutables) | Riesgo menor documentado |
| R10 | LogReturn vía float | Deuda TD-04 |
| R11 | Processed JSONL / catálogo SQLite → Parquet/DuckDB | Deuda TD-01/TD-02 |
| R12 | `mark_equity` 2× por barra | Funcional; cleanup menor (TD-12) |
| R13 | ORDER ROUTING LIVE | **BLOQUEADO** por diseño |

---

## 📎 Certificados de fase vigentes

- `docs/audit/FASE_02_APPROVED.md`
- `docs/audit/FASE_03_APPROVED.md`
- `docs/audit/FASE_04_APPROVED.md`
- `docs/audit/FASE_05_OFFICIAL_APPROVED.md`
- Deuda: `docs/TECHNICAL_DEBT.md`

---

## 🔓 Conclusión

El avance de hardening F2–F5 + correcciones nocturnas queda **validado por suite automatizada**.  
No se emitió certificado de fases nuevas posteriores a F5.  
**ORDER ROUTING REAL / LIVE** permanece **BLOQUEADO**.
