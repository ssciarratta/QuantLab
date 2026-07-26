# Fase 76 — Broker Reconnect Button

**Estado:** ✅ **APROBADO_INTERNO** (v0.68.0) — certificado externo `FASE_76_APPROVED.md` **NO** emitido  
**Base:** v0.67.0 · F75 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-120  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F76.md` · noche `INTERNAL_AUDIT_F19_F76_NIGHT.md`

## Objetivo

Exponer **`POST /api/broker/reconnect`**: re-ejecuta los últimos params de connect guardados en session meta (`last_broker_connect`). Al conectar, se persiste la config. Botón **Reconectar** en Market Data y Health. Sin flip LIVE.

## DoD

- [x] Persist `last_broker_connect` en `meta.json` al `POST /api/broker/connect`
- [x] `POST /api/broker/reconnect` — re-run last connect (400 si no hay config)
- [x] UI botón Reconectar en Market (`#md-reconnect`) + Health (`#hp-reconnect`)
- [x] Docs: `docs/FASE_76_RECONNECT.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_broker_reconnect_f76.py`
- [x] Smoke F76 · DEC-120 · bump **0.68.0**
- [x] Sin `FASE_76_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| POST | `/api/broker/connect` | Persiste `last_broker_connect` en meta (venue, mode, md_source, csv_path?, slippage_bps?) |
| POST | `/api/broker/reconnect` | Body vacío; reutiliza meta; respuesta incluye `reconnect: true` |

### Respuesta reconnect (éxito)

| Campo | Valor |
|-------|-------|
| `ok` | true |
| `reconnect` | true |
| `kind` | `broker_reconnect` |
| `venue` / `mode` / `md_source` | de last connect |
| `has_last_connect` | true |
| `live_blocked` | true (vía connect path) |

### Errores

| Caso | HTTP | Mensaje |
|------|------|---------|
| Sin last connect | 400 | `no hay config de connect previa; POST /api/broker/connect primero` |

## UI / JS

| Pieza | Rol |
|-------|-----|
| `#md-reconnect` | Market Data — Reconectar |
| `#hp-reconnect` | Health — Reconectar |
| `QLApi.reconnect()` | `POST /api/broker/reconnect` |

## Meta key

```json
{
  "last_broker_connect": {
    "venue": "binance",
    "mode": "tester",
    "md_source": "fake",
    "slippage_bps": "0"
  },
  "last_broker_connect_updated_at": "ISO-8601"
}
```

## Fuera de alcance

LIVE · auth WAN · certificado externo `FASE_76_APPROVED.md` · auto-reconnect en heartbeat fail · credentials secretas en meta
