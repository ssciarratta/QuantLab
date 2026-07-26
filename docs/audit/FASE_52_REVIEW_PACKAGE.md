# FASE 52 — Review Package INTERNAL

**Fecha:** 2026-07-26  
**Versión código (impl F52):** 0.44.0  
**Impl SHA:** `feace00`  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Certificado externo:** **NO** (`FASE_52_APPROVED.md` no emitido)

## Resumen

Graceful shutdown del Workbench: SIGINT/SIGTERM + `POST /api/shutdown` (solo loopback) detienen paper session, flushean layout/settings/book y apagan el HTTPServer. DEC-096 · bump 0.44.0.

## Artefactos

| ID | Item | Path |
|----|------|------|
| A1 | Módulo shutdown | `src/quantlab/workbench/shutdown.py` |
| A2 | launch signals | `src/quantlab/workbench/launch.py` |
| A3 | API shutdown | `api.py` / `server.py` |
| A4 | Suite | `tests/unit/workbench/test_shutdown_f52.py` |
| A5 | Spec | `docs/FASE_52_SHUTDOWN.md` |
| A6 | Version 0.44.0 | `pyproject.toml` |
| A7 | DEC-096 | `learning/decisiones.txt` |

## QA

```text
uv run mypy --strict src/quantlab     → 178 ok
uv run ruff check src/quantlab tests scripts
uv run pytest -q                      → 866 passed
uv run quantlab-health                → ok=true, live_blocked=true, version=0.44.0
uv run python scripts/internal_audit_smoke.py  → 38/38 PASS
```

## Invariantes

- `LIVE_BLOCKED is True`
- `phases_summary == "F19–F52 INTERNAL"`
- Sin flip LIVE
- Sin `FASE_52_APPROVED.md`
