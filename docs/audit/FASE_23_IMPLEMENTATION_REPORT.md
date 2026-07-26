# FASE 23 — Implementation Report (Paper Book + Session + Risk)

**Fecha:** 2026-07-26  
**Versión:** 0.15.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F22 Chat IA v0.14.0  
**Alcance:** PaperBook realista + sesión durable + risk paper — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| B1 | `PaperBook` | `brokers/paper/book.py` |
| B2 | `PaperBroker` + book | `brokers/paper/broker.py` |
| B3 | `WorkbenchSession` | `workbench/session.py` |
| B4 | `PaperRiskLimits` | `workbench/risk.py` |
| B5 | API positions/book/session | `workbench/api.py` + `server.py` |
| B6 | Launch flags sesión/cash | `workbench/launch.py` |
| B7 | Panel Posiciones + banner | `static/js/panes/positions.js`, `shell.js` |
| B8 | Suite unit | `tests/unit/brokers/test_paper_book.py`, `tests/unit/workbench/test_*` |
| B9 | Spec DoD | `docs/FASE_23_PAPER_BOOK.md` |
| B10 | Bump | `pyproject.toml` + `__version__` → 0.15.0 |

## Invariantes

- `LIVE_BLOCKED is True`
- Short rechazado por defecto (`allow_short=False`)
- Paper submit pasa por `PaperRiskLimits.check_intent`
- `PaperBroker` no llama `md_port.submit`
- Session recoverable bajo `data/runtime/workbench/<id>/`

## QA

```text
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/brokers tests/unit/workbench
uv run ruff check src/quantlab tests/unit/brokers tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/brokers tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- MD real A3 (F24)
- Launcher .desktop (F25)

## Audit INTERNAL (post-impl)

- Autauditoría: `docs/audit/AUTO_AUDIT_2026-07-26_F23.md`
- Review Package INTERNAL: `docs/audit/FASE_23_REVIEW_PACKAGE.md`
- Veredicto: `docs/audit/INTERNAL_AUDIT_F23.md` = **APROBADO_INTERNO**
- Remediación: H1 `validate_session_id` · H2 cash/shorts fail-closed en load
- **No** emitir `FASE_23_APPROVED.md` desde INTERNAL
