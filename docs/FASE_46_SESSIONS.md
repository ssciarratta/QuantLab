# Fase 46 — Multi-Session Switcher

**Estado:** ✅ **APROBADO_INTERNO** (v0.38.0) — certificado externo `FASE_46_APPROVED.md` **NO** emitido  
**Base:** v0.37.0 · F45 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-090  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F46.md` · noche `INTERNAL_AUDIT_F19_F46_NIGHT.md`

## Objetivo

Listar, crear y cambiar entre sesiones durables del workbench bajo el session root, con validación fail-closed de `session_id` y recreación de paths (journal/book/labs).

## DoD

- [x] API `GET /api/sessions` — lista session dirs bajo session root
- [x] API `POST /api/sessions/switch` `{session_id}` — switch fail-closed + recrea paths
- [x] API `POST /api/sessions/new` — crea sesión nueva y switch
- [x] UI panel Sessions (menú Inicio / `open.sessions`)
- [x] Docs: `docs/FASE_46_SESSIONS.md` + IMPLEMENTATION_REPORT
- [x] Tests + QA
- [x] DEC-090 · bump **0.38.0**
- [x] Sin `FASE_46_APPROVED.md`

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/sessions` | lista dirs válidos + `current` |
| POST | `/api/sessions/switch` | body `{session_id}` · 404 si no existe · 400 si inválido |
| POST | `/api/sessions/new` | body opcional `{session_id}` · UUID corto si omitido |

Respuestas incluyen `live_blocked:true`. Switch detiene paper runner, persiste book, limpia broker MD y chat, hidrata journal/book/labs de la nueva sesión.

## UI

- Menú Inicio → Sistema → **Sessions** (`data-open="sessions"`)
- Command palette: `open.sessions`
- Panel: listar / Cambiar / Nueva sesión
- Script: `static/js/panes/sessions.js` → `QLPanes.createSessionsPane`
- Client: `QLApi.sessionsList` / `sessionsSwitch` / `sessionsNew`

## Notas técnicas

- `list_sessions` + `validate_session_id` en `workbench/session.py`
- `WorkbenchState.session_parent` · `switch_session` · `new_session`
- Paths recreados vía `_hydrate_from_session`
- `phases_summary` tip: `F19–F46 INTERNAL`

## Fuera de alcance

LIVE · auth WAN · Electron · certificado externo `FASE_46_APPROVED.md` · browser E2E · delete/rename session
