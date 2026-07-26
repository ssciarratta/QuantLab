# Fase 79 — Watchlist Import/Export JSON

**Estado:** ✅ **APROBADO_INTERNO** (v0.71.0) — certificado externo `FASE_79_APPROVED.md` **NO** emitido  
**Base:** v0.70.0 · F78 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-123  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F79.md` · noche `INTERNAL_AUDIT_F19_F79_NIGHT.md`

## Objetivo

Export e import de la watchlist de sesión como JSON: descarga server-side y merge/replace vía API + botones en el panel Universe — sin flip LIVE.

## DoD

- [x] `GET /api/watchlist/export` → `application/json; charset=utf-8` + `Content-Disposition: attachment`
- [x] Payload canónico `{version, symbols}` (mismo shape que `watchlist.json`)
- [x] `POST /api/watchlist/import` `{symbols:[...], mode: "merge"|"replace"}` (default merge)
- [x] Acepta también `{watchlist: {symbols:[...]}}`
- [x] Botones **Export JSON** / **Import JSON** en Universe (`universe.js`)
- [x] `QLApi.watchlistExportUrl()` · `QLApi.importWatchlist(body)`
- [x] OpenAPI catalog routes
- [x] Docs: `docs/FASE_79_WATCHLIST_IO.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_watchlist_io_f79.py` + smoke F79
- [x] DEC-123 · bump **0.71.0**
- [x] Sin `FASE_79_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/watchlist` | JSON watchlist (F30) |
| PUT | `/api/watchlist` | add/remove/replace (F30) |
| GET | `/api/watchlist/export` | JSON download attachment |
| POST | `/api/watchlist/import` | merge (dedupe add) o replace |

### Import body

```json
{"symbols": ["GGAL", "YPFD"], "mode": "merge"}
```

| Campo | Default | Notas |
|-------|---------|-------|
| `symbols` | — | lista (requerida, o vía `watchlist.symbols`) |
| `mode` | `merge` | `merge` = add/dedupe; `replace` = sustituye lista |

## UI

| Control | Acción |
|---------|--------|
| `#un-export` | Descarga `/api/watchlist/export` |
| `#un-import-file` | File picker `.json` |
| `#un-import-mode` | merge / replace |
| `#un-import` | POST import + refresh |

## Notas técnicas

- Filename: `quantlab-watchlist-<session_id>.json`
- Validación fail-closed (charset, max 256, version=1)
- No toca venue submit / LIVE

## Fuera de alcance

LIVE · auth WAN · multi-watchlist named · certificado externo `FASE_79_APPROVED.md` · browser E2E
