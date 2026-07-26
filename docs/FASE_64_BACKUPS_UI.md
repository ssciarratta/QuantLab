# Fase 64 — Backups Panel UI

**Estado:** ✅ **APROBADO_INTERNO** (v0.56.0) — certificado externo `FASE_64_APPROVED.md` **NO** emitido  
**Base:** v0.55.0 · F63 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-108  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F64.md` · noche `INTERNAL_AUDIT_F19_F64_NIGHT.md`

## Objetivo

Panel Workbench que lista backups de sesión (`GET /api/backups`) y dispara backup manual (`POST /api/backups/run` → `run_auto_backup`), con entrada en menú Inicio y command palette — sin flip LIVE.

## DoD

- [x] Panel Backups (`static/js/panes/backups.js`) → `QLApi.getBackups` / `QLApi.runBackup`
- [x] Botón **Backup ahora** → `POST /api/backups/run`
- [x] Lista filename · bytes · mtime · sha256 (más recientes arriba)
- [x] Meta: `auto_backup_minutes` · session_id · LIVE_BLOCKED (settings F63)
- [x] Menú Inicio → Sistema → **Backups**
- [x] Command palette `open.backups`
- [x] i18n key `pane.backups` (es/en)
- [x] Docs: `docs/FASE_64_BACKUPS_UI.md` + IMPLEMENTATION_REPORT
- [x] Tests UI + API `test_backups_ui_f64.py` + smoke F64
- [x] DEC-108 · bump **0.56.0**
- [x] Sin `FASE_64_APPROVED.md` · sin LIVE

## UI

| Elemento | Detalle |
|----------|---------|
| Menú | Inicio → Sistema → Backups |
| Palette | `open.backups` · keywords backup / zip / respaldo |
| Acciones | **Backup ahora** + Actualizar |
| Lista | filename · bytes · mtime_utc · sha256 corto |
| Meta | auto_backup_minutes · session_id · LIVE_BLOCKED |

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/backups` | Lista ZIPs (F63) |
| POST | `/api/backups/run` | Trigger manual `run_auto_backup` + sidecar sha + lista |

## Notas técnicas

- Reutiliza `run_auto_backup` / allowlist F39 + zip-slip; rotación max 5
- Settings `auto_backup_minutes` permanece en backend (F63); el panel muestra el valor
- Activity log: kind `backup` en trigger manual

## Fuera de alcance

LIVE · auth WAN · restore one-click · download ZIP desde panel · certificado externo `FASE_64_APPROVED.md` · browser E2E
