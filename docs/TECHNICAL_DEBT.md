# QuantLab — Technical Debt

**Actualizado:** 2026-07-25 (Fase 18 Control Total código)  
**Propósito:** Deudas residuales conocidas.  
**Certificados / reports:** `FASE_*_APPROVED.md`, `FASE_18_IMPLEMENTATION_REPORT.md`

| ID | Deuda | Fase sugerida | Severidad | Notas |
|----|-------|---------------|-----------|-------|
| TD-01 | ~~Processed solo JSONL~~ | F17 | — | Mitigado |
| TD-02 | ~~Sin DuckDB catalog~~ | F17 | — | Mitigado |
| TD-03 | Contabilidad / ledger distribuido multi-nodo | F17+/futuro | Alta | Fuera de F18 local |
| TD-04 | ~~LogReturn float~~ | F18 | — | Mitigado: `Decimal.ln` |
| TD-05 | Latencia wall-clock (`min_delay`) no implementada | F7 | Media | Se rechaza si `min_delay>0` |
| TD-06 | ~~AlphaScanner sin explicabilidad~~ | F18+audit | — | Mitigado: drivers con w×contrib |
| TD-07 | ~~MetricsEngine sin reporting HTML~~ | F8 | — | Mitigado |
| TD-08 | ~~Experiment Registry CRUD incompleto~~ | F9 | — | Mitigado |
| TD-09 | FeatureStore filesystem local; sin backend remoto | F17 | Baja | — |
| TD-10 | Order routing LIVE A3 bloqueado por diseño | N/A | — | Irrenunciable |
| TD-11 | ~~Forward-fill sesga volatilidad AlphaScanner~~ | F18+audit | — | Mitigado: vol/liq solo `volume>0` |
| TD-12 | `mark_equity` 2× por barra | F4 | Baja | Intencional: pre-ctx vs post-trade (comentado en engine) |
| TD-13 | ~~Colisión path FeatureStore~~ | F18 | — | Mitigado: hashed segments |
| TD-14 | ~~verify_dataset hash~~ | research-prod | — | Mitigado |
| TD-15 | ~~profit_factor=999~~ | research-prod | — | Mitigado |
| TD-16 | ~~Sortino vs Sharpe~~ | research-prod | — | Mitigado |
| TD-17 | ~~Fees fuera de realized_pnl~~ | F18 | — | Convención: `gross_excluding_fees` |
| TD-18 | ~~zip-slip restore~~ | research-prod | — | Mitigado |

## Notas

- F18: paper ledger local ≠ ledger distribuido (TD-03).
- CI Actions: `docs/ci/ci.yml.example` hasta scope OAuth `workflow`.
