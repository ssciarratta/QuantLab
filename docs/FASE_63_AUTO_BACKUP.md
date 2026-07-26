# Fase 63 — Session Auto-Backup

**Estado:** ✅ **APROBADO_INTERNO** (v0.55.0) — certificado externo `FASE_63_APPROVED.md` **NO** emitido  
**Base:** v0.54.0 · F62 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-107  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F63.md` · noche `INTERNAL_AUDIT_F19_F63_NIGHT.md`

## Objetivo

Auto-backup opcional de la sesión activa como ZIP research-safe (misma allowlist F39), con rotación acotada — sin flip LIVE.

## DoD

- [x] Settings `auto_backup_minutes` (default **0=off**; si >0, scheduler background)
- [x] Export ZIP → `session/backups/` · rotación **max 5**
- [x] `GET /api/backups` lista
- [x] Reusa `session_zip.export_session` (allowlist + zip-slip fail-closed · sin secretos)
- [x] Trigger manual `run_auto_backup()` para tests
- [x] Docs: `docs/FASE_63_AUTO_BACKUP.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_auto_backup_f63.py` + smoke F63
- [x] DEC-107 · bump **0.55.0**
- [x] Sin `FASE_63_APPROVED.md` · sin LIVE

## Settings

| Campo | Default | Notas |
|-------|---------|-------|
| `auto_backup_minutes` | `0` | `0` = off; rango `0..1440` |

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/backups` | Lista ZIPs en `session/backups/` (más recientes primero) |

## Notas técnicas

- Scheduler daemon arranca en `create_server`; stop en graceful shutdown
- `backups/` **no** está en la allowlist de export → no anida ZIPs
- Primer ciclo tras activar: backup inmediato; luego cada N minutos
- Fail-soft: errores del scheduler no tumban el HTTP server

## Fuera de alcance

LIVE · auth WAN · UI panel de backups · restore one-click · certificado externo `FASE_63_APPROVED.md`
