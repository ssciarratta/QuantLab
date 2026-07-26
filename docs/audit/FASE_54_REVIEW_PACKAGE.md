# FASE 54 — Review Package INTERNAL

**Fecha:** 2026-07-26  
**Versión código (impl F54):** 0.46.0  
**Impl SHA:** `(pending commit)`  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Certificado externo:** **NO** (`FASE_54_APPROVED.md` no emitido)

## Resumen

Probes HTTP del Workbench: `GET /api/livez` (liveness, siempre 200 si proceso up) y `GET /api/readyz` (readiness: 200 si LIVE_BLOCKED + session root writable; 503 si no). Documentado para Docker HEALTHCHECK. DEC-098 · bump 0.46.0.

## Artefactos

| ID | Item | Path |
|----|------|------|
| A1 | Probes | `src/quantlab/workbench/probes.py` |
| A2 | Routes | `server.py` · `api.py` |
| A3 | Ops | `docs/ops/DOCKER_WORKBENCH.md` |
| A4 | Suite | `tests/unit/workbench/test_probes_f54.py` |
| A5 | Spec | `docs/FASE_54_PROBES.md` |
| A6 | Version 0.46.0 | `pyproject.toml` |
| A7 | DEC-098 | `learning/decisiones.txt` |

## QA

```text
uv run mypy --strict src/quantlab     → 179 ok
uv run ruff check src/quantlab tests scripts
uv run pytest -q                      → 884 passed
uv run quantlab-health                → ok=true, live_blocked=true, version=0.46.0
uv run python scripts/internal_audit_smoke.py  → 40/40 PASS
```

## Invariantes

- `LIVE_BLOCKED is True`
- `phases_summary == "F19–F54 INTERNAL"`
- Sin flip LIVE
- Sin `FASE_54_APPROVED.md`
