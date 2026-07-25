# QuantLab — Technical Debt

**Actualizado:** 2026-07-24 (post F6 5A)  
**Propósito:** Deudas residuales conocidas tras hardening F2–F6.  
**Certificados:** `NIGHT_AUDIT_2026-07-24.md`, `FASE_06_APPROVED.md`

| ID | Deuda | Fase sugerida | Severidad | Notas |
|----|-------|---------------|-----------|-------|
| TD-01 | Processed storage aún JSONL; migrar a Parquet columnar | F17 | Media | Protocolo `CatalogBackend` ya desacopla consultas |
| TD-02 | Catálogo SQLite; DuckDB como motor analítico primario | F17 | Media | `SqliteCatalogBackend` implementa el protocol |
| TD-03 | Contabilidad / ledger distribuido y reconciliación multi-nodo | F17 | Alta | — |
| TD-04 | LogReturn usa `math.log` vía float (no Decimal puro) | F5+/numéricas | Baja | — |
| TD-05 | Latencia wall-clock (`min_delay`) no implementada | F7 | Media | Ahora se rechaza si `min_delay>0` |
| TD-06 | AlphaScanner sin explicabilidad completa de scores | F13 | Baja | Gaps + liquidez sin sintéticas |
| TD-07 | MetricsEngine sin reporting HTML | F8 | Media | Sortino/Calmar ya en motor |
| TD-08 | Experiment Registry CRUD incompleto (ArtifactsEngine parcial) | F9 | Media | — |
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

## Notas

- No confundir “F5 local ejecución” (slippage/fees/artifacts) con **F5 Oficial Features**.
- Certificados: `docs/audit/FASE_02_APPROVED.md` … `FASE_05_OFFICIAL_APPROVED.md` + night audit.
