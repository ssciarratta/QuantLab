# Fase 74 — Status Bar Clock Timezone

**Estado:** ✅ **APROBADO_INTERNO** (v0.66.0) — certificado externo `FASE_74_APPROVED.md` **NO** emitido  
**Base:** v0.65.0 · F73 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-118  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F74.md` · noche `INTERNAL_AUDIT_F19_F74_NIGHT.md`

## Objetivo

Preferencia de sesión **`timezone`** (default **`"UTC"`**; opciones **`UTC`** / **`local`**) que controla el reloj de la status bar vía JS (`toLocaleTimeString` con `timeZone: "UTC"` o zona local del navegador). Sin flip LIVE.

## DoD

- [x] Settings `timezone: "UTC"` default · opciones UTC / local · persistido en `settings.json`
- [x] Select UI en panel Settings
- [x] Status bar clock respeta setting (JS)
- [x] Docs: `docs/FASE_74_CLOCK_TZ.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_clock_timezone_f74.py` (roundtrip settings)
- [x] Smoke F74 · DEC-118 · bump **0.66.0**
- [x] Sin `FASE_74_APPROVED.md` · sin LIVE

## Settings

| Campo | Tipo | Default | Valores |
|-------|------|---------|---------|
| `timezone` | string | `"UTC"` | `UTC` \| `local` |

## UI / JS

| Pieza | Rol |
|-------|-----|
| Settings select `#set-timezone` | Preferencia UTC / local |
| `setClockTimezone` (shell) | Hidrata flag desde settings (boot + pane save) |
| `tickClock` | `toLocaleTimeString` · si UTC → `timeZone: "UTC"` + sufijo ` UTC` |

## Fuera de alcance

LIVE · auth WAN · certificado externo `FASE_74_APPROVED.md` · IANA timezones arbitrarias · sync NTP
