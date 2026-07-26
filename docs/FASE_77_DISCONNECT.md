# Fase 77 — Broker Disconnect + Milestone prep

**Estado:** ✅ **APROBADO_INTERNO** (v0.69.0) — certificado externo `FASE_77_APPROVED.md` **NO** emitido  
**Base:** v0.68.0 · F76 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-121  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F77.md` · noche `INTERNAL_AUDIT_F19_F77_NIGHT.md`

## Objetivo

Exponer **`POST /api/broker/disconnect`**: cierra el broker, limpia el estado conectado (`broker` / `venue` / `md_*`) y **conserva** `last_broker_connect` en session meta para poder reconectar. Botón **Desconectar** en Market Data y Health. Prep hacia milestone v0.70. Sin flip LIVE.

## DoD

- [x] `POST /api/broker/disconnect` — close broker + clear connected state
- [x] Conserva `last_broker_connect` (reconnect sigue funcionando)
- [x] Idempotente si ya estaba desconectado
- [x] UI botón Desconectar en Market (`#md-disconnect`) + Health (`#hp-disconnect`)
- [x] Docs: `docs/FASE_77_DISCONNECT.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_broker_disconnect_f77.py`
- [x] Smoke F77 · DEC-121 · bump **0.69.0**
- [x] Sin `FASE_77_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| POST | `/api/broker/disconnect` | Body vacío; cierra broker; mantiene last connect |
| POST | `/api/broker/reconnect` | (F76) reutiliza last connect post-disconnect |

### Respuesta disconnect (éxito)

| Campo | Valor |
|-------|-------|
| `ok` | true |
| `disconnect` | true |
| `kind` | `broker_disconnect` |
| `was_connected` | true/false |
| `previous_venue` | venue previo o null |
| `connected` | false |
| `has_last_connect` | true si hay meta |
| `last_connect` | config o null |
| `live_blocked` | true |

## UI / JS

| Pieza | Rol |
|-------|-----|
| `#md-disconnect` | Market Data — Desconectar |
| `#hp-disconnect` | Health — Desconectar |
| `QLApi.disconnect()` | `POST /api/broker/disconnect` |

## Fuera de alcance

LIVE · auth WAN · certificado externo `FASE_77_APPROVED.md` · wipe de `last_broker_connect` · milestone freeze v0.70 (prep only)
