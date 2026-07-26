# FASE 52 — Implementation Report (Graceful Shutdown + Paper Session Safety)

**Fecha:** 2026-07-26  
**Versión:** 0.44.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F51 APROBADO_INTERNO  
**Impl SHA:** *(tip post-commit)*  
**Alcance:** graceful shutdown workbench — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Módulo shutdown | `src/quantlab/workbench/shutdown.py` |
| D2 | SIGINT/SIGTERM + finally | `src/quantlab/workbench/launch.py` |
| D3 | API POST `/api/shutdown` loopback | `api.py` + `server.py` |
| D4 | Suite F52 | `tests/unit/workbench/test_shutdown_f52.py` |
| D5 | Spec + DEC-096 + bump | `docs/FASE_52_SHUTDOWN.md` · `0.44.0` |
| D6 | Smoke F52 | `scripts/internal_audit_smoke.py` |
| D7 | Bundle default to-phase 52 | `scripts/build_internal_review_bundle.py` |
| D8 | Implementation report | este doc |

## Comportamiento

- **Señales:** SIGINT/SIGTERM llaman `perform_graceful_shutdown` → `serve_forever` retorna.
- **API:** `POST /api/shutdown` solo si peer loopback; marca flag y programa `server.shutdown()`.
- **Paper safety:** runner `stop()` + `paper_session = None` antes del flush.
- **Flush:** re-persiste `layout.json` / `settings.json` (sync `slippage_bps`) + `book` si hay.
- **Idempotente:** segundo call no vuelve a schedulear shutdown.

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_52_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-096
- `phases_summary == "F19–F52 INTERNAL"`
- About `version` ≡ `__version__` == `0.44.0`

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff check src/quantlab tests scripts
uv run mypy --strict src/quantlab
uv run pytest -q
uv run quantlab-health                     # 0.44.0 · live_blocked=true
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Certificado externo `FASE_52_APPROVED.md`
