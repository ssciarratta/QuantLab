# FASE 39 — Implementation Report (Session Export/Import ZIP)

**Fecha:** 2026-07-26  
**Versión:** 0.31.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F38 Docs/Help · F36 Settings · F23 Session durable  
**Alcance:** export/import ZIP sesión — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Session ZIP core (export/import/zip-slip) | `workbench/session_zip.py` |
| A1 | `GET /api/session/export` · `POST /api/session/import` | `api.py` + `server.py` |
| U1 | Botones Export/Import en Settings | `static/js/panes/settings.js` |
| U2 | API client | `static/js/api.js` |
| T1 | Tests F39 | `tests/unit/workbench/test_session_zip_f39.py` |
| T2 | Smoke F39 | `scripts/internal_audit_smoke.py` |
| D2 | Spec + DEC-083 + bump | `docs/FASE_39_SESSION_ZIP.md` · `0.31.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Secretos nunca en ZIP de export; rechazados en import
- Zip-slip → `ValidationError` (vía `scale.backup._assert_safe_zip_member`)
- Merge no overwrite (fail-closed)
- DEC-083

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_session_zip_f39.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Certificado externo `FASE_39_APPROVED.md`
- Merge con overwrite
