# FASE 46 — Review Package INTERNAL (Multi-Session Switcher)

**Fecha:** 2026-07-26  
**Versión código (impl F46):** 0.38.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Impl SHA:** `ce9cbdd`  
**LIVE:** BLOQUEADO  
**Certificado externo:** **NO** (`FASE_46_APPROVED.md` no emitido)

---

## Resumen ejecutivo

Multi-session switcher: listar sesiones bajo session root, cambiar con fail-closed `validate_session_id`, crear nueva y switch; UI panel Sessions. DEC-090.

**Opción elegida:** APIs `/api/sessions*` + panel WM + recreación de paths en WorkbenchState; sin delete/rename; sin LIVE.

## Entregables

| ID | Entrega | Path |
|----|---------|------|
| A1 | list_sessions | `workbench/session.py` |
| A2 | switch/new state + handlers | `api.py` · `server.py` |
| A3 | UI Sessions | `sessions.js` · `shell.js` · `index.html` · CSS |
| A4 | Spec | `docs/FASE_46_SESSIONS.md` |
| A5 | Implementation report | `docs/audit/FASE_46_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-090 | `learning/decisiones.txt` |
| A7 | Version 0.38.0 | `pyproject.toml` |
| A8 | Suite F46 | `tests/unit/workbench/test_sessions_f46.py` |
| A9 | Smoke F46 | `scripts/internal_audit_smoke.py` |
| A10 | Bundle to-phase 46 | `scripts/build_internal_review_bundle.py` |

## Evidencia QA

```
uv run mypy --strict src/quantlab     → Success: 175 files
uv run ruff check                     → All checks passed
uv run pytest -q                      → 827 passed
uv run quantlab-health                → ok=true, live_blocked=true, version=0.38.0
uv run python scripts/internal_audit_smoke.py → 32/32 PASS
```

## Smoke API (síntesis)

| # | Endpoint | Esperado |
|---|----------|----------|
| 1 | GET /api/sessions | 200 · kind=sessions · live_blocked |
| 2 | POST /api/sessions/switch | 200 · session_id · paths hidratados |
| 3 | POST /api/sessions/new | 200 · created |
| 4 | POST switch `../evil` | 400 fail-closed |
| 5 | POST switch missing | 404 |

## Fuera de alcance

LIVE · auth WAN · Electron · browser E2E · delete session · `FASE_46_APPROVED.md`

## Veredicto INTERNAL propuesto

**APROBADO_INTERNO** — ver `INTERNAL_AUDIT_F46.md`.
