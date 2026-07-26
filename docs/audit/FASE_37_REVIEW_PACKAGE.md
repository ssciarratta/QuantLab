# FASE 37 — Review Package INTERNAL (First-run Onboarding Wizard)

**Fecha:** 2026-07-26  
**Versión código (impl F37):** 0.29.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** flag `onboarding_done` en session `meta.json` vía `workbench/onboarding.py`; API `GET /api/onboarding` + `POST /api/onboarding/complete`; wizard modal SPA 4 pasos (TESTER/REAL/LIVE bloqueado → venue tester → Paper/Backtest → Chat IA safe). DEC-081.

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Persistencia | `workbench/onboarding.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Wizard JS | `static/js/onboarding.js` |
| A4 | Boot + CSS | `shell.js` · `api.js` · `index.html` · CSS |
| A5 | Spec | `docs/FASE_37_ONBOARDING.md` |
| A6 | Implementation report | `docs/audit/FASE_37_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-081 | `learning/decisiones.txt` |
| A8 | Suite F37 | `tests/unit/workbench/test_onboarding_f37.py` |
| A9 | Version 0.29.0 | `pyproject.toml` |
| A10 | Impl SHA | `81ff9b1` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.29.0
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

LIVE flip · auth WAN · browser E2E · certificado externo `FASE_37_APPROVED.md`
