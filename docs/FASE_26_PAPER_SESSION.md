# Fase 26 — Paper Session Runner

**Estado:** IMPLEMENTADO (v0.18.0) — audit externo pendiente  
**Base:** v0.17.0 · F19–F25 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)

## Objetivo
Sesión paper operativa en workbench: elegir estrategia → generar `OrderIntent` sobre MD del broker conectado → ejecutar vía PaperBroker (risk+slip+book) → ver blotter/posiciones en vivo.

## DoD
- [x] `PaperSessionRunner` (start/stop/step)
- [x] Estrategias: Dummy / BuyOnce / SimpleMomentum (research existentes)
- [x] API `/api/paper/session/*`
- [x] Panel UI “Sesión Paper”
- [x] Nunca place_order venue
- [x] Tests + LIVE_BLOCKED
- [x] Bump **0.18.0**

## API
| Método | Path | Body / notas |
|--------|------|----------------|
| POST | `/api/paper/session/start` | `strategy_id`, `symbol`, `max_steps?`, `interval_ms?`, `params?` |
| POST | `/api/paper/session/stop` | — |
| POST | `/api/paper/session/step` | tick manual |
| GET | `/api/paper/session/status` | `running`, `steps`, `last_error`, `strategy_id` |

Requiere broker conectado (`PaperBroker`). Modos `tester|paper`.

## Background
Si `interval_ms` en start: thread daemon llama `step` hasta `max_steps` o `stop` (cancelable). Tests usan solo step manual.

## Fuera de alcance
LIVE · WS streaming exchange real · auto-flip
