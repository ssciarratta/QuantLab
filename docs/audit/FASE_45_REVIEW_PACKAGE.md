# FASE 45 — Review Package INTERNAL (About Dialog + Version Badge)

**Fecha:** 2026-07-26  
**Versión código (impl F45):** 0.37.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** endpoint read-only `GET /api/about` + badge en status bar + modal About (menú Inicio / command palette), sin ventana WM ni LIVE. DEC-089.

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | About module | `src/quantlab/workbench/about.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | UI About + badge | `static/js/about.js` · `shell.js` · `index.html` · CSS |
| A4 | Spec | `docs/FASE_45_ABOUT.md` |
| A5 | Implementation report | `docs/audit/FASE_45_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-089 | `learning/decisiones.txt` |
| A7 | Version 0.37.0 | `pyproject.toml` |
| A8 | Suite F45 | `tests/unit/workbench/test_about_f45.py` |
| A9 | Smoke F45 | `scripts/internal_audit_smoke.py` |
| A10 | Bundle to-phase 45 | `scripts/build_internal_review_bundle.py` |
| A11 | Impl SHA | `a103236` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest tests/unit/workbench/test_about_f45.py -q
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.37.0
uv run python scripts/internal_audit_smoke.py
```

## Criterios fail-hard

| # | Criterio | Esperado |
|---|----------|----------|
| 1 | LIVE_BLOCKED | True |
| 2 | GET /api/about | 200 · version 0.37.0 · phases F19–F45 INTERNAL |
| 3 | bind_policy loopback | `loopback-default` en fixture |
| 4 | UI assets | about.js · sb-version · Acerca de |
| 5 | FASE_45_APPROVED.md | **NO** creado |

## Fuera de alcance

Certificado externo · LIVE flip · auth WAN · browser E2E
