# Fase 41 — Activity Log + Toasts

**Estado:** ✅ **APROBADO_INTERNO** (v0.33.0) — certificado externo `FASE_41_APPROVED.md` **NO** emitido  
**Base:** v0.32.0 · F40 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-085  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F41.md` · noche `INTERNAL_AUDIT_F19_F41_NIGHT.md`

## Objetivo
Log append-only de actividad de sesión (`activity.jsonl`) con eventos clave del workbench, API de lectura, toasts UI y panel Activity — sin flip LIVE.

## DoD
- [x] `activity.jsonl` append-only en sesión (events: connect, submit, backtest, optimize, export, error)
- [x] API `GET /api/activity?limit=100`
- [x] Hooks mínimos en handlers clave
- [x] UI: toasts success/error + panel Activity
- [x] Docs: `docs/FASE_41_ACTIVITY.md` + IMPLEMENTATION_REPORT
- [x] Tests + QA
- [x] DEC-085 · bump **0.33.0**
- [x] Sin `FASE_41_APPROVED.md` · sin LIVE

## Eventos

| event | Origen |
|-------|--------|
| `connect` | `POST /api/broker/connect` OK |
| `submit` | `POST /api/paper/submit` OK |
| `backtest` | `POST /api/lab/backtest` OK |
| `optimize` | `POST /api/lab/optimize` OK |
| `export` | `GET /api/session/export` / `POST /api/session/import` OK |
| `error` | fallo ApiError en ops anteriores (`op` = connect\|submit\|…) |

Cada línea JSONL: `ts`, `event`, `ok`, `message`, `live_blocked`, opcional `op` / `detail`.

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/activity?limit=100` | Últimos N eventos (default 100, max 500) |

Respuesta: `ok`, `kind:activity`, `count`, `events`, `event_types`, `session_id`, `live_blocked`, `live_routing:false`, `research_safe:true`.

## UI

- Toasts (esquina inferior derecha) en connect / submit / backtest / optimize / export / import
- Menú Inicio → Sistema → **Activity**
- Panel: lista reciente + refresh; command palette `open.activity`

## Notas técnicas
- Módulo: `workbench/activity.py` · `ActivityLog`
- Persistencia: `session/activity.jsonl` (también en ZIP export F39)
- Append best-effort: fallos de log no tumban la API

## Fuera de alcance
LIVE · auth WAN · Electron · certificado externo `FASE_41_APPROVED.md` · browser E2E · rewrite/truncate del log
