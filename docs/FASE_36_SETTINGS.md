# Fase 36 — Settings + Status Bar

**Estado:** ✅ **APROBADO_INTERNO** (v0.28.0) — certificado externo `FASE_36_APPROVED.md` **NO** emitido  
**Base:** v0.27.0 · F35 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-080  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F36.md` · noche `INTERNAL_AUDIT_F19_F36_NIGHT.md`

## Objetivo
Preferencias durables por sesión (`settings.json`) + panel Settings + status bar fija inferior (mode, live_blocked, session_id, venue, md_provider, clock). Temas `slate` | `high-contrast`; locale `es`.

## DoD
- [x] `settings.json` por sesión: theme, default_venue, default_strategy, slippage_bps, locale=es
- [x] API `GET/PUT /api/settings`
- [x] Panel Settings UI
- [x] Status bar fija inferior
- [x] Docs: `docs/FASE_36_SETTINGS.md` + IMPLEMENTATION_REPORT
- [x] Tests API settings + smoke; JS vía presencia API/static
- [x] DEC-080 · bump **0.28.0**

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/settings` | settings + session_id / mode / venue / md_provider |
| PUT | `/api/settings` | merge parcial fail-closed → `settings.json` |

Respuesta incluye: `settings{}`, `live_blocked`, `live_routing:false`, `research_safe:true`, `allowed_themes`, `allowed_locales`.

PUT actualiza también `state.slippage_bps`.  
**No** incluye flip LIVE / place_order / set_live.

## Settings schema

| Campo | Tipo | Default | Notas |
|-------|------|---------|-------|
| version | int | 1 | |
| theme | slate\|high-contrast | slate | CSS `data-theme` |
| default_venue | str | paper | charset venue |
| default_strategy | str | momentum | catálogo F27 (+ aliases) |
| slippage_bps | decimal str | 0 | ≥0 · <10000 |
| locale | es | es | solo `es` |

## UI

- Panel Settings (start menu Sistema · command palette `open.settings`)
- Status bar inferior fija: mode · live_blocked · session_id · venue · md_provider · clock
- Theme high-contrast vía variables CSS

## Notas técnicas
- Persistencia en `workbench/settings.py` (fuente de verdad)
- Path: `data/runtime/workbench/<session_id>/settings.json`
- Client: `QLApi.getSettings` / `putSettings`

## Fuera de alcance
LIVE · auth WAN · Electron · certificado externo `FASE_36_APPROVED.md` · browser E2E · locales distintos de `es`
