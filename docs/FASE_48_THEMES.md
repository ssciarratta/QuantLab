# Fase 48 — Theme CSS Completion (slate + high-contrast)

**Estado:** ✅ **APROBADO_INTERNO** (v0.40.0) — certificado externo `FASE_48_APPROVED.md` **NO** emitido  
**Base:** v0.39.0 · F47 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-092  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F48.md` · noche `INTERNAL_AUDIT_F19_F48_NIGHT.md`

## Objetivo

Completar el sistema de temas CSS del workbench: tokens completos para `slate` (default) y `high-contrast`, aplicados vía `data-theme` en `documentElement` (+ body) al cargar settings y al `PUT /api/settings`. Settings ya existían desde F36; F48 cierra el chrome (banner / status / taskbar / desktop / overlays).

## DoD

- [x] CSS variables completas para `slate` | `high-contrast` (chrome + semantic)
- [x] `data-theme` en `documentElement` (+ body) al load settings y al PUT settings
- [x] Default `data-theme="slate"` en `index.html`
- [x] Smoke + tests theme roundtrip
- [x] Docs: `docs/FASE_48_THEMES.md` + IMPLEMENTATION_REPORT
- [x] DEC-092 · bump **0.40.0**
- [x] Sin `FASE_48_APPROVED.md`
- [x] `LIVE_BLOCKED is True`

## Themes

| Theme | Rol |
|-------|-----|
| `slate` | Default — deep slate + amber |
| `high-contrast` | Negro puro + bordes blancos + amarillo alto contraste |

## Tokens (subset)

`--bg-*` (deep/panel/elevated/title/banner/status/taskbar/desktop) · `--border*` · `--text*` · `--amber*` · `--danger` · `--ok` · `--warn` · `--accent` · `--hover-surface*` · `--overlay*` · `--shadow-win` · `--shadow-modal`

## UI / JS

- `shell.js` `applyTheme` al boot (`getSettings`) y callback Settings
- `settings.js` `applyTheme` en `render()` (load + tras PUT)
- Select Tema en panel Settings (F36)

## Notas técnicas

- Fuente de verdad settings: `workbench/settings.py` · `ALLOWED_THEMES`
- CSS: `static/css/workbench.css` — `:root` / `html[data-theme="slate"]` + `html[data-theme="high-contrast"]`
- `phases_summary` tip: `F19–F48 INTERNAL`

## Fuera de alcance

LIVE · auth WAN · Electron · certificado externo `FASE_48_APPROVED.md` · locales ≠ `es` · themes adicionales
