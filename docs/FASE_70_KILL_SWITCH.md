# Fase 70 — Paper Kill Switch

**Estado:** ✅ **APROBADO_INTERNO** (v0.62.0) — certificado externo `FASE_70_APPROVED.md` **NO** emitido  
**Base:** v0.61.0 · F69 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-114  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F70.md` · noche `INTERNAL_AUDIT_F19_F70_NIGHT.md`

## Objetivo

Enganche de **kill switch paper-only**: cuando `engaged`, rechazar paper submit y session step con `ValidationError`, persistir flag en session meta, API + botón rojo en Risk/Sesión Paper — sin flip LIVE.

## DoD

- [x] `WorkbenchState.paper_kill_engaged` + `assert_paper_kill_clear()` → `ValidationError`
- [x] Reject `POST /api/paper/submit` + `POST /api/paper/session/step` cuando engaged
- [x] `POST /api/paper/kill` `{engaged: bool}` · `GET /api/paper/kill` status
- [x] Persist `paper_kill_engaged` en `meta.json`
- [x] Big red ENGAGE/DISENGAGE en Risk + Sesión Paper
- [x] OpenAPI catalog routes
- [x] Docs: `docs/FASE_70_KILL_SWITCH.md` + IMPLEMENTATION_REPORT
- [x] Tests `test_paper_kill_f70.py` + smoke F70
- [x] DEC-114 · bump **0.62.0**
- [x] Sin `FASE_70_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/paper/kill` | `{engaged, session_id, blocks, live_blocked,…}` |
| POST | `/api/paper/kill` | Body `{engaged: bool}` — persiste meta |

### Convención

- Engaged → `ValidationError("paper kill switch engaged — …")` envuelto en `ApiError 400`
- Bloquea: paper submit + paper session step
- No bloquea: stop session, book/fills reads, risk utilization, LIVE (ya bloqueado)

## UI

| Panel | Acción |
|-------|--------|
| Risk | Sección **Paper Kill Switch** — botón rojo ENGAGE/DISENGAGE |
| Sesión Paper | Misma acción kill (engage/disengage) |

## Fuera de alcance

LIVE · auth WAN · certificado externo `FASE_70_APPROVED.md` · hard-stop automático del runner al engage · browser E2E
