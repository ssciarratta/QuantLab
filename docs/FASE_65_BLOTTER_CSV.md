# Fase 65 — Blotter CSV Server Export

**Estado:** ✅ **APROBADO_INTERNO** (v0.57.0) — certificado externo `FASE_65_APPROVED.md` **NO** emitido  
**Base:** v0.56.0 · F64 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-109  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F65.md` · noche `INTERNAL_AUDIT_F19_F65_NIGHT.md`

## Objetivo

Export server-side de fills del journal paper como `text/csv` (`GET /api/paper/fills.csv`) con botón de descarga en Blotter y Journal — sin flip LIVE.

## DoD

- [x] `GET /api/paper/fills.csv` → `text/csv; charset=utf-8` + `Content-Disposition: attachment`
- [x] Header estable: `ts,fill_id,order_id,symbol,side,quantity,price,source`
- [x] Rows desde `PaperFillJournal.list_fills()` / `export_csv()`
- [x] Botón **Descargar CSV** en Blotter (`blotter.js`) y Journal (`journal.js`)
- [x] `QLApi.paperFillsCsvUrl()` → `/api/paper/fills.csv`
- [x] OpenAPI catalog route
- [x] Docs: `docs/FASE_65_BLOTTER_CSV.md` + IMPLEMENTATION_REPORT
- [x] Tests header + rows `test_fills_csv_f65.py` + smoke F65
- [x] DEC-109 · bump **0.57.0**
- [x] Sin `FASE_65_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/paper/fills` | JSON fills (F20/F28) |
| GET | `/api/paper/fills.csv` | CSV download del mismo journal |

## UI

| Panel | Acción |
|-------|--------|
| Journal | **Descargar CSV** → servidor; **CSV local** (vista) se mantiene |
| Blotter | **Descargar CSV** → servidor |

## Notas técnicas

- Escapado RFC-like: comillas/comas/newlines en campos
- Filename: `quantlab-fills-<session_id>.csv`
- No toca venue submit / LIVE

## Fuera de alcance

LIVE · auth WAN · filtros/columnas custom · certificado externo `FASE_65_APPROVED.md` · browser E2E
