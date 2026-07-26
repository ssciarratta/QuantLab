# FASE 36 — Review Package INTERNAL (Settings + Status Bar)

**Fecha:** 2026-07-26  
**Versión código (impl F36):** 0.28.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** `settings.json` por sesión vía `workbench/settings.py`; API `GET/PUT /api/settings` con merge parcial fail-closed; panel Settings SPA; status bar fija inferior (mode, live_blocked, session_id, venue, md_provider, clock). Themes `slate`|`high-contrast`; locale `es` (DEC-080).

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Persistencia | `workbench/settings.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Panel Settings | `static/js/panes/settings.js` |
| A4 | Status bar + shell | `static/index.html` · `shell.js` · CSS |
| A5 | Spec | `docs/FASE_36_SETTINGS.md` |
| A6 | Implementation report | `docs/audit/FASE_36_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-080 | `learning/decisiones.txt` |
| A8 | Suite F36 | `tests/unit/workbench/test_settings_f36.py` |
| A9 | Version 0.28.0 | `pyproject.toml` |
| A10 | Impl SHA | `2c0cb11` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.28.0
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

LIVE flip · auth WAN · browser E2E · certificado externo `FASE_36_APPROVED.md`
