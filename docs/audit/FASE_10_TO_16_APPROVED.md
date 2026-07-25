# Certificado Fases 10–16 — MVP autónomo nocturno

- **Estado**: 🟢 APROBADO (MVP de cierre de roadmap v1)
- **Fecha**: 2026-07-25
- **Versión proyecto**: 0.8.0

| Fase | Módulo | Path principal |
|------|--------|----------------|
| 10 | Scientific Validation | `quantlab.validation` |
| 11 | Monte Carlo | `quantlab.montecarlo` |
| 12 | Optimizer grid/random | `quantlab.optimizer` |
| 13 | Alpha explain | `research.alpha.explain` |
| 14 | Position sizing | `research.sizing` |
| 15 | Generic CSV provider | `data.exchanges.generic_csv` |
| 16 | Hummingbot export (LIVE blocked) | `execution_export` |

## Residuos cerrados después (ver FASE_17_APPROVED)
- F10 multiple testing, F12 Pareto, F14 Avellaneda — certificados en `docs/audit/FASE_17_APPROVED.md` (2026-07-25)

## No incluido
- CI GitHub Actions (requiere PAT con scope `workflow`) — ver `docs/ci/ci.yml.example`
- Order routing LIVE: **BLOQUEADO**
- Ledger multi-nodo (TD-03)

## QA
- pytest / mypy --strict / ruff: PASSED (suite integral)
