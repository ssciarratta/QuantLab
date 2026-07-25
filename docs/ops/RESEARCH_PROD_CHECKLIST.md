# Checklist Research-Prod QuantLab

Marcar tras cada agente. **Trading-prod / LIVE real: N/A (bloqueado).**

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Remote git sin token embebido + PAT revocado | ✅ | Remote limpio; `ghp_*` revocado; GCM borrado; git vía `gh` |
| 2 | Secret scan incluye remote URL | ✅ | `scripts/check_git_remote_clean.py` |
| 3 | LIVE fail-closed en A3Adapter + PyRofexBackend | ✅ | `_enforce_live_blocked` + `assert_live_routing_blocked` en place/cancel |
| 4 | `execution.enabled` default false | ✅ | `config/exchanges/a3.yaml` |
| 5 | NullRouter default / sin send_order accidental | ✅ | `execution/order_router.py`; A3Adapter default NullRouter |
| 6 | Batch strict + monitor Lock + Parquet atómico | ✅ | `ParallelBatchRunner(strict=True)`; WAL; `.tmp`+`os.replace` |
| 7 | verify_dataset hashea storage | ✅ | SQLite + DuckDB backends recalculan SHA-256 |
| 8 | Accounting fails on orphan fills | ✅ | `assert_accounting_balanced` → ValidationError |
| 9 | Métricas sin sentinel 999 | ✅ | `profit_factor` → `"undefined"` / `None` |
| 10 | CI workflow activo o bloqueo documentado | ✅ | `.github/workflows/ci.yml` restaurado desde `docs/ci/ci.yml.example` |
| 11 | Docs roadmap alineadas | ✅ | `docs/Roadmap.md` apunta a `ROADMAP_ALIGNED.md` |
| 12 | Suite pytest + mypy strict + ruff verdes | ✅ | Gate post-hardening 2026-07-25 |

**Definition of Research-Prod Ready:** todos ✅ excepto filas N/A; LIVE sigue BLOQUEADO.

**Nota:** no emitir nuevo `FASE_*_APPROVED` por este hardening; no habilitar LIVE.
