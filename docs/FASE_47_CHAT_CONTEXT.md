# Fase 47 — Chat Context Awareness

**Estado:** ✅ **APROBADO_INTERNO** (v0.39.0) — certificado externo `FASE_47_APPROVED.md` **NO** emitido  
**Base:** v0.38.0 · F46 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-091  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F47.md` · noche `INTERNAL_AUDIT_F19_F47_NIGHT.md`

## Objetivo

Extender el chat safe-by-default con awareness de contexto de sesión (resumen, reports, catálogo de estrategias), **sin** tools de trading ni mutaciones LIVE.

## DoD

- [x] Tools allowlist: `get_session_summary`, `list_reports`, `list_strategies`
- [x] FakeProvider patterns ES («cómo estoy», «resumen sesión», «qué reportes hay», «estrategias»)
- [x] Illegal tools siguen rechazados; new tools ejecutan
- [x] Docs: `docs/FASE_47_CHAT_CONTEXT.md` + IMPLEMENTATION_REPORT
- [x] Tests + QA
- [x] DEC-091 · bump **0.39.0**
- [x] Sin `FASE_47_APPROVED.md`
- [x] Chat **sin** trading tools

## Tools nuevas (read-only)

| Tool | Rol |
|------|-----|
| `get_session_summary` | mode, venue, book equity, positions count, activity last N |
| `list_reports` | reports lab persistidos de la sesión (`list_lab_reports`) |
| `list_strategies` | catálogo workbench (`list_strategy_catalog`) |

## FakeProvider (ES)

| Intent | Tool |
|--------|------|
| «¿cómo estoy?» / «resumen sesión» | `get_session_summary` |
| «qué reportes hay» | `list_reports` |
| «estrategias» | `list_strategies` |

## Seguridad

- `LIVE_BLOCKED is True` (sin flip)
- Allowlist disjoint de `FORBIDDEN_TOOLS` (`submit_order`, `place_order`, `set_live`, …)
- `chat_mutations: false` en payloads nuevos
- Sin `FASE_47_APPROVED.md`

## Notas técnicas

- `ToolRegistry` en `workbench/chat/tools.py`
- Activity vía `list_activity` + `clamp_limit` (default N=10)
- `phases_summary` tip: `F19–F47 INTERNAL`

## Fuera de alcance

LIVE · auth WAN · Electron · certificado externo `FASE_47_APPROVED.md` · trading tools en chat · LLM HTTP de producción
