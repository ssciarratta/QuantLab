# Fase 37 — First-run Onboarding Wizard

**Estado:** ✅ **APROBADO_INTERNO** (v0.29.0) — certificado externo `FASE_37_APPROVED.md` **NO** emitido  
**Base:** v0.28.0 · F36 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-081  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F37.md` · noche `INTERNAL_AUDIT_F19_F37_NIGHT.md`

## Objetivo
Wizard modal de primer arranque cuando la sesión no tiene `onboarding_done` en `meta.json`. Orienta modos TESTER/REAL/LIVE (LIVE bloqueado), conectar venue tester, Sesión Paper/Backtest y Chat IA safe.

## DoD
- [x] Si meta sin `onboarding_done` → mostrar wizard modal (4 pasos)
- [x] Paso 1: TESTER vs REAL vs LIVE (LIVE bloqueado)
- [x] Paso 2: conectar venue tester
- [x] Paso 3: abrir Sesión Paper / Backtest
- [x] Paso 4: Chat IA safe
- [x] API `GET /api/onboarding` + `POST /api/onboarding/complete`
- [x] Docs: `docs/FASE_37_ONBOARDING.md` + IMPLEMENTATION_REPORT
- [x] Tests + smoke; JS vía presencia API/static
- [x] DEC-081 · bump **0.29.0**

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/onboarding` | status: `onboarding_done`, `show_wizard`, steps, modes |
| POST | `/api/onboarding/complete` | set `onboarding_done=true` en `meta.json` (idempotente) |

Respuesta incluye: `live_blocked`, `live_routing:false`, `research_safe:true`, `steps[]`, `modes{}`.

**No** incluye flip LIVE / place_order / set_live.

## Meta schema

| Campo | Tipo | Default | Notas |
|-------|------|---------|-------|
| onboarding_done | bool | ausente/false | truthy → wizard oculto |
| onboarding_completed_at | ISO-8601 str | — | set al completar |

## UI

- Modal overlay `#onboarding-wizard` (z-index sobre palette)
- 4 pasos con progress dots + CTAs a paneles (Market / Paper / Backtest / Chat)
- Completar / Omitir → `POST /api/onboarding/complete`
- Boot en `shell.js` tras session/settings

## Notas técnicas
- Persistencia: `workbench/onboarding.py` sobre `meta.json` de sesión
- Path: `data/runtime/workbench/<session_id>/meta.json`
- Client: `QLApi.getOnboarding` / `completeOnboarding`
- Script: `static/js/onboarding.js` → `QLOnboarding`

## Fuera de alcance
LIVE · auth WAN · Electron · certificado externo `FASE_37_APPROVED.md` · browser E2E · forzar pasos (wizard es orientativo)
