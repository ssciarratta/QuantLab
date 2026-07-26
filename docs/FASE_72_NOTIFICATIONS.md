# Fase 72 — Desktop Notifications Hook

**Estado:** ✅ **APROBADO_INTERNO** (v0.64.0) — certificado externo `FASE_72_APPROVED.md` **NO** emitido  
**Base:** v0.63.0 · F71 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-116  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F72.md` · noche `INTERNAL_AUDIT_F19_F72_NIGHT.md`

## Objetivo

Preferencia de sesión **`desktop_notifications`** (default **false**) que, cuando está activa, dispara la **Notification API** del navegador ante toasts de error y al **engage** del paper kill switch — con degradación graceful si el permiso es denegado o la API no está disponible. Sin flip LIVE.

## DoD

- [x] Settings `desktop_notifications: false` default · persistido en `settings.json`
- [x] Checkbox UI en panel Settings
- [x] Cuando true → Notification API en toast errors + kill engage
- [x] Graceful si `Notification` ausente / permission denied / insecure context
- [x] Docs: `docs/FASE_72_NOTIFICATIONS.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_desktop_notifications_f72.py` (roundtrip settings)
- [x] Smoke F72 · DEC-116 · bump **0.64.0**
- [x] Sin `FASE_72_APPROVED.md` · sin LIVE

## Settings

| Campo | Tipo | Default |
|-------|------|---------|
| `desktop_notifications` | bool | `false` |

## UI / JS

| Pieza | Rol |
|-------|-----|
| Settings checkbox | Toggle opt-in |
| `QLToasts.setDesktopNotifications` | Hidrata flag desde settings (shell + pane) |
| `QLToasts.error` | Si enabled → `new Notification(...)` |
| `QLToasts.notifyKillEngage` | Tras `POST /api/paper/kill` con `engaged=true` |

## Fuera de alcance

LIVE · auth WAN · certificado externo `FASE_72_APPROVED.md` · browser E2E de Notification permission · push service workers
