# FASE 40 — Review Package INTERNAL (Workspace Presets)

**Fecha:** 2026-07-26  
**Versión código (impl F40):** 0.32.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** módulo `workbench/presets.py` con tres layouts built-in; `GET /api/presets` + `POST /api/presets/apply` que reescribe `layout.json` vía `save_layout`; UI en menú Inicio → Espacios de trabajo. DEC-084.

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Presets core | `workbench/presets.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Start menu Espacios | `static/index.html` · `shell.js` |
| A4 | API client + closeAll | `static/js/api.js` · `wm.js` |
| A5 | Spec | `docs/FASE_40_PRESETS.md` |
| A6 | Implementation report | `docs/audit/FASE_40_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-084 | `learning/decisiones.txt` |
| A8 | Suite F40 | `tests/unit/workbench/test_presets_f40.py` |
| A9 | Version 0.32.0 | `pyproject.toml` |
| A10 | Impl SHA | `8197f32` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.32.0
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

LIVE flip · auth WAN · browser E2E · certificado externo `FASE_40_APPROVED.md` · presets custom
