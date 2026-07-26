# FASE 43 — Review Package INTERNAL (Red-team Workbench Hardening)

**Fecha:** 2026-07-26  
**Versión código (impl F43):** 0.35.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** auditoría red-team de superficies HTTP workbench + remediación fail-closed in-place (sandbox `zip_path`, gate loopback en `create_server`, body 2 MiB, reject traversal en ids/docs/csv). DEC-087.

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Server hardening | `workbench/server.py` |
| A2 | Session ZIP sandbox | `session_zip.py` · `api.py` |
| A3 | Launch loopback re-export | `launch.py` |
| A4 | Spec | `docs/FASE_43_REDTEAM.md` |
| A5 | Implementation report | `docs/audit/FASE_43_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-087 | `learning/decisiones.txt` |
| A7 | Suite F43 | `tests/unit/workbench/test_redteam_f43.py` |
| A8 | Version 0.35.0 | `pyproject.toml` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest tests/unit/workbench/test_redteam_f43.py -q
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.35.0
uv run python scripts/internal_audit_smoke.py
```

## Criterios fail-hard

| # | Criterio | Esperado |
|---|----------|----------|
| 1 | LIVE_BLOCKED | True |
| 2 | zip_path fuera sandbox | 400 / ValidationError |
| 3 | create_server 0.0.0.0 sin flag | ValidationError |
| 4 | POST mode=live | 400 |
| 5 | body > 2 MiB | 400 |
| 6 | FASE_43_APPROVED.md | **NO** creado |

## Fuera de alcance

Certificado externo · LIVE flip · auth WAN · browser E2E
