# QuantLab — Technical Debt

**Actualizado:** 2026-07-25 (cierre residuales no críticos self-audit)  
**Propósito:** Deudas residuales conocidas.  
**Certificados / reports:** `FASE_*_APPROVED.md`, `FASE_18_IMPLEMENTATION_REPORT.md`

| ID | Deuda | Fase sugerida | Severidad | Notas |
|----|-------|---------------|-----------|-------|
| TD-01 | ~~Processed solo JSONL~~ | F17 | — | Mitigado |
| TD-02 | ~~Sin DuckDB catalog~~ | F17 | — | Mitigado |
| TD-03 | ~~Federación shards paper ledger~~ | F18+ | — | Mitigado research: `node_id` + `reconcile`/`merge_from`. Residual: ACID multi-nodo / HA cluster (trading-prod) |
| TD-04 | ~~LogReturn float~~ | F18 | — | Mitigado: `Decimal.ln` |
| TD-05 | ~~Latencia wall-clock (`min_delay`)~~ | F18+ | — | Mitigado: `FixedLatencyModel` + `bar_times` en engine |
| TD-06 | ~~AlphaScanner sin explicabilidad~~ | F18+audit | — | Mitigado: drivers con n/w/contrib/share; `contrib_sum == composite` |
| TD-07 | ~~MetricsEngine sin reporting HTML~~ | F8 | — | Mitigado |
| TD-08 | ~~Experiment Registry CRUD incompleto~~ | F9 | — | Mitigado |
| TD-09 | ~~FeatureStore filesystem local~~ | F17 | — | Aceptado research-prod: rechazo URL remota; sin S3 |
| TD-10 | Order routing LIVE A3 bloqueado por diseño | N/A | — | Irrenunciable |
| TD-11 | ~~Forward-fill sesga volatilidad AlphaScanner~~ | F18+audit | — | Mitigado: vol/liq solo `volume>0` |
| TD-12 | ~~`mark_equity` 2× por barra~~ | F4 | — | Mitigado/diseño: pre-ctx + post-trade; test regresión |
| TD-13 | ~~Colisión path FeatureStore~~ | F18 | — | Mitigado: hashed segments |
| TD-14 | ~~verify_dataset hash~~ | research-prod | — | Mitigado |
| TD-15 | ~~profit_factor=999~~ | research-prod | — | Mitigado |
| TD-16 | ~~Sortino vs Sharpe~~ | research-prod | — | Mitigado |
| TD-17 | ~~Fees fuera de realized_pnl~~ | F18 | — | Convención: `gross_excluding_fees` |
| TD-18 | ~~zip-slip restore~~ | research-prod | — | Mitigado |

## Residuales de convención (self-audit, cerrados 2026-07-25)

| ID | Tema | Estado |
|----|------|--------|
| R3 | ATR = SMA de TR (no Wilder) | ✅ Doc + `metadata.method=sma_tr` |
| R5 | Calmar anualiza por #puntos | ✅ Doc + test bar-based |
| R9 | `freeze_mapping` nested mutable | ✅ Deep-freeze |
| OPS-PROM | Contadores sin export | ✅ `render_prometheus_text` |

## Notas

- TD-03 residual trading-prod: cluster HA / ledger ACID distribuido — fuera de research-prod.
- CI Actions: `.github/workflows/ci.yml` versionado (fuente espejo `docs/ci/ci.yml.example`).
- LIVE / TD-10 y `FASE_18_APPROVED` no se “cierran” desde research-prod.
