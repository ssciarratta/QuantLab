# Fase 73 — Optional Sound Alerts

**Estado:** ✅ **APROBADO_INTERNO** (v0.65.0) — certificado externo `FASE_73_APPROVED.md` **NO** emitido  
**Base:** v0.64.0 · F72 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-117  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F73.md` · noche `INTERNAL_AUDIT_F19_F73_NIGHT.md`

## Objetivo

Preferencia de sesión **`sound_alerts`** (default **false**) que, cuando está activa, dispara un **beep corto vía Web Audio API** ante toasts de error y al **engage** del paper kill switch — sin assets externos, con degradación graceful si `AudioContext` no está disponible. Sin flip LIVE.

## DoD

- [x] Settings `sound_alerts: false` default · persistido en `settings.json`
- [x] Checkbox UI en panel Settings
- [x] Cuando true → WebAudio beep en toast errors + kill engage
- [x] Graceful si `AudioContext` ausente / autoplay blocked
- [x] Docs: `docs/FASE_73_SOUND.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_sound_alerts_f73.py` (roundtrip settings)
- [x] Smoke F73 · DEC-117 · bump **0.65.0**
- [x] Sin `FASE_73_APPROVED.md` · sin LIVE

## Settings

| Campo | Tipo | Default |
|-------|------|---------|
| `sound_alerts` | bool | `false` |

## UI / JS

| Pieza | Rol |
|-------|-----|
| Settings checkbox | Toggle opt-in |
| `QLToasts.setSoundAlerts` | Hidrata flag desde settings (shell + pane) |
| `QLToasts.error` | Si enabled → `playBeep()` (OscillatorNode ~140ms) |
| `QLToasts.notifyKillEngage` | Tras `POST /api/paper/kill` con `engaged=true` → beep |

## Fuera de alcance

LIVE · auth WAN · certificado externo `FASE_73_APPROVED.md` · archivos WAV/MP3 · browser E2E de AudioContext autoplay
