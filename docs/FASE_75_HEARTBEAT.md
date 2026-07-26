# Fase 75 — Broker Heartbeat Status

**Estado:** ✅ **APROBADO_INTERNO** (v0.67.0) — certificado externo `FASE_75_APPROVED.md` **NO** emitido  
**Base:** v0.66.0 · F74 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-119  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F75.md` · noche `INTERNAL_AUDIT_F19_F75_NIGHT.md`

## Objetivo

Exponer **`GET /api/broker/heartbeat`**: si hay broker conectado llama `broker.health()`; si no, responde `disconnected`. La status bar muestra **ok/fail** y el shell hace poll cada **N=5** segundos. Sin flip LIVE.

## DoD

- [x] `GET /api/broker/heartbeat` — health() si conectado; else disconnected (HTTP 200)
- [x] Status bar item `#sb-heartbeat` · clases ok/fail
- [x] Shell poll cada **N=5** s (`HEARTBEAT_POLL_SECONDS` / `poll_seconds`)
- [x] Docs: `docs/FASE_75_HEARTBEAT.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_broker_heartbeat_f75.py`
- [x] Smoke F75 · DEC-119 · bump **0.67.0**
- [x] Sin `FASE_75_APPROVED.md` · sin LIVE

## API

| Campo | disconnected | ok | fail |
|-------|--------------|----|------|
| `ok` | false | true | false |
| `status` | `disconnected` | `ok` | `fail` |
| `heartbeat` | `fail` | `ok` | `fail` |
| `connected` | false | true | true |
| `health` | null | dict | dict\|null |
| `poll_seconds` | 5 | 5 | 5 |

## UI / JS

| Pieza | Rol |
|-------|-----|
| `#sb-heartbeat` | Texto `ok` / `fail` / `disconnected` |
| `pollBrokerHeartbeat` | `QLApi.brokerHeartbeat()` cada N s |
| CSS `.sb-heartbeat.ok` / `.fail` | Color ok / danger |

## Fuera de alcance

LIVE · auth WAN · certificado externo `FASE_75_APPROVED.md` · N configurable vía settings UI
