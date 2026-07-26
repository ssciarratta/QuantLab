# FASE 39 — Review Package INTERNAL (Session Export/Import ZIP)

**Fecha:** 2026-07-26  
**Versión código (impl F39):** 0.31.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

## Decisión de diseño

**Opción elegida:** módulo `workbench/session_zip.py` con allowlist de archivos/dirs de sesión, exclusión de secretos, zip-slip vía `scale.backup._assert_safe_zip_member`, escritura atómica; API `GET /api/session/export` (JSON o `?download=1`) + `POST /api/session/import` (`new`|`merge` fail-closed); UI en Settings. DEC-083.

## Artefactos A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Session ZIP core | `workbench/session_zip.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Settings Export/Import | `static/js/panes/settings.js` |
| A4 | API client | `static/js/api.js` |
| A5 | Spec | `docs/FASE_39_SESSION_ZIP.md` |
| A6 | Implementation report | `docs/audit/FASE_39_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-083 | `learning/decisiones.txt` |
| A8 | Suite F39 | `tests/unit/workbench/test_session_zip_f39.py` |
| A9 | Version 0.31.0 | `pyproject.toml` |
| A10 | Impl SHA | `0cb9d7a` |

## QA esperado

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health                → ok=true, live_blocked=true, version=0.31.0
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

LIVE flip · auth WAN · browser E2E · certificado externo `FASE_39_APPROVED.md` · merge overwrite
