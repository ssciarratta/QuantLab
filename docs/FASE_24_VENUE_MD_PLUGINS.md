# Fase 24 — Venue plugins + MD read-only multiplataforma

**Estado:** IMPLEMENTADO (v0.16.0)  
**Prerrequisito:** F23 (v0.15.0 Paper Book)  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)

## Objetivo
- Entry-points `quantlab.brokers` para registrar cualquier venue sin tocar builtins
- A3 MD read-only real/sandbox opt-in (PAPER/REAL); submit sigue gated
- Generic REST/CSV MD skeleton documentado
- Workbench reporta `md_provider`

## DoD
- [x] `load_entry_point_brokers(registry)` — grupo `quantlab.brokers`; fallas → warning, no crash
- [x] `get_default_registry()` carga plugins además de builtins
- [x] A3 `md_source`: `fake` | `env` (env requiere `QUANTLAB_A3_MD_READONLY=1` + `QUANTLAB_A3_*`; fallback fake)
- [x] A3 submit/cancel siempre `assert_live_routing_blocked`
- [x] `generic_csv` + `generic_rest` builtins MD-only
- [x] Workbench connect acepta `md_source`; health/session reportan `md_provider` / `plugin_venues`
- [x] UI Market muestra provider
- [x] Tests: plugins, a3 md fallback, generic, live blocked
- [x] Docs: `docs/ops/BROKER_PLUGINS.md` + DEC-067..068
- [x] Bump **0.16.0**; `LIVE_BLOCKED is True`

## Fuera de alcance
Órdenes venue · flip LIVE · F25 Ops Desk
