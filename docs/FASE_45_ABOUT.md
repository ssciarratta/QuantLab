# Fase 45 — About Dialog + Version Badge

**Estado:** ✅ **APROBADO_INTERNO** (v0.37.0) — certificado externo `FASE_45_APPROVED.md` **NO** emitido  
**Base:** v0.36.0 · F44 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-089  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F45.md` · noche `INTERNAL_AUDIT_F19_F45_NIGHT.md`

## Objetivo

Exponer metadatos de versión / fases INTERNAL / Python / bind policy vía API, y mostrar badge de versión en la status bar con diálogo **Acerca de** desde el menú Inicio.

## DoD

- [x] API `GET /api/about` — version, live_blocked, phases_summary, python_version, bind_policy
- [x] Badge versión en status bar (click → About)
- [x] Diálogo About (menú Inicio → Acerca de) + command palette `open.about`
- [x] Docs: `docs/FASE_45_ABOUT.md` + IMPLEMENTATION_REPORT
- [x] Tests + QA
- [x] DEC-089 · bump **0.37.0**
- [x] Sin `FASE_45_APPROVED.md`

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/about` | read-only metadata |

Respuesta incluye: `version`, `live_blocked`, `phases_summary` (`F19–F45 INTERNAL`), `python_version`, `bind_policy` (loopback-default / allow-non-loopback), `live_routing:false`, `research_safe:true`.

**No** incluye flip LIVE / place_order / secretos.

## UI

- Status bar: badge `vX.Y.Z` (`#sb-version`) — click abre About
- Menú Inicio → **Acerca de** (`data-open="about"`)
- Command palette: `open.about`
- Script: `static/js/about.js` → `QLAbout.open`
- Client: `QLApi.about`

## Notas técnicas

- Módulo: `workbench/about.py`
- `WorkbenchState.bind_host` / `allow_non_loopback` poblados por `create_server`
- Modal (no ventana WM) — patrón similar a onboarding

## Fuera de alcance

LIVE · auth WAN · Electron · certificado externo `FASE_45_APPROVED.md` · browser E2E
