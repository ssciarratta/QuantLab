# QuantLab — Technical Debt

**Actualizado:** 2026-07-25 (post F17 MVP + residuos)  
**Propósito:** Deudas residuales conocidas tras hardening F2–F17 código.  
**Certificados / reports:** `FASE_*_APPROVED.md`, `FASE_17_IMPLEMENTATION_REPORT.md`

| ID | Deuda | Fase sugerida | Severidad | Notas |
|----|-------|---------------|-----------|-------|
| TD-01 | ~~Processed solo JSONL~~ | F17 | — | Mitigado: `ParquetProcessedStore` (JSONL sigue disponible) |
| TD-02 | ~~Sin DuckDB catalog~~ | F17 | — | Mitigado: `DuckDBCatalogBackend` (SQLite sigue default) |
| TD-03 | Contabilidad / ledger distribuido y reconciliación multi-nodo | F17+ | Alta | Fuera de MVP F17 local |
| TD-04 | LogReturn usa `math.log` vía float (no Decimal puro) | F5+/numéricas | Baja | — |
| TD-05 | Latencia wall-clock (`min_delay`) no implementada | F7 | Media | Ahora se rechaza si `min_delay>0` |
| TD-06 | AlphaScanner sin explicabilidad completa de scores | F13 | Baja | Gaps + liquidez; explain MVP en F13 |
| TD-07 | ~~MetricsEngine sin reporting HTML~~ | F8 | — | Mitigado: ReportGenerator HTML (night run) |
| TD-08 | ~~Experiment Registry CRUD incompleto~~ | F9 | — | Mitigado: ExperimentRegistry MVP |
| TD-09 | FeatureStore filesystem local; sin backend remoto | F17 | Baja | Writes atómicos OK |
| TD-10 | Order routing LIVE A3 bloqueado por diseño | N/A (gate) | — | Irrenunciable |
| TD-11 | Forward-fill crea barras sintéticas (volumen 0) | F4+/research | Baja | Liquidez ya ignora volume==0 |
| TD-12 | `mark_equity` se invoca 2× por barra en el engine | F4 cleanup | Baja | Funcional |
| TD-13 | Colisión path FeatureStore (`a/b` ↔ `a_b`) | F5+/store | Baja | Requiere hash de segmentos |
| TD-14 | `verify_dataset` no recalcula hash de storage | F3+/catalog | Media | Solo valida formato SHA-256 |
| TD-15 | `profit_factor=999.0` sentinel | F8 | Baja | Distorsiona rankings |
| TD-16 | Sortino `/N` vs Sharpe `/(N-1)` | F8 | Baja | Convención pendiente unificar |
| TD-17 | Fees fuera de `realized_pnl` bruto | F4+/accounting | Baja | Confirmar convención |

## Resuelto / mitigado (no deuda abierta)

- Infinity/NaN en Decimal de dominio → rechazo
- Fill cross-instrumento → `instrument_mismatch`
- Order LIMIT price post-slippage → conserva límite
- Latencia: contexto pre-fill → due fills antes de StrategyContext
- FeatureStore path `..` → rechazo; writes atómicos
- Validators multi-instrumento falsos OOO → estado por instrumento
- Slippage bps≥10000 → rechazo
- Causal timestamps iguales → rechazo
- Alpha liquidez inflada por FFILL → ignora volume==0
- MARKET 5B stale `last_px` → L2 Best Bid/Ask primero (2026-07-25)
- Slippage solo lineal en libro → `SlippageMode.SQUARE_ROOT` (2026-07-25)
- Resting huérfanas sin TTL → `resting_max_age_ticks` + `TTL_EXPIRED` (2026-07-25)
- 5A mono-instrumento forzado → sync multi-activo por `timestamp_close` (2026-07-25)
- F17 paralelismo/monitor/backup/100K probe (2026-07-25)
- F10 multiple testing Bonferroni/Holm/BH (2026-07-25)
- F12 Pareto front (2026-07-25)
- F14 Avellaneda–Stoikov MVP (2026-07-25)
- Parquet + DuckDB catalog backends (2026-07-25)

## Notas

- No confundir “F5 local ejecución” (slippage/fees/artifacts) con **F5 Oficial Features**.
- Certificados: `docs/audit/FASE_02_APPROVED.md` … `FASE_05_OFFICIAL_APPROVED.md` + night audit.
