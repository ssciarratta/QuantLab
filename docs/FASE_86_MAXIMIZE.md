# Fase 86 — Maximize / Restore Window

**Estado:** ✅ **APROBADO_INTERNO** (v0.78.0) — certificado externo `FASE_86_APPROVED.md` **NO** emitido  
**Base:** v0.77.0 · F85 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-130  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F86.md` · noche `INTERNAL_AUDIT_F19_F86_NIGHT.md`

## Objetivo

Maximize / Restore de ventanas MDI: **maximize(id)** guarda geometría pre-max y llena el workspace; **restoreFromMaximize(id)** restaura; dblclick titlebar / botón titlebar / palette / menú Inicio; persistir `maximized` en layout — sin flip LIVE.

## DoD

- [x] `wm.js`: `maximize(id)` / `restoreFromMaximize(id)` / `toggleMaximize(id)` + store `preMax`
- [x] Double-click titlebar toggles maximize
- [x] Titlebar button □ / ❐
- [x] Command palette: `action.maximize_window` · `action.restore_from_maximize`
- [x] Menú Inicio: grupo **Ventanas** con ambos botones (`data-wm-action`)
- [x] Context menu titlebar: Maximize / Restore
- [x] Persist `maximized` (+ pre-max como x/y/w/h) en layout; restore vía `mergeOpts` / `open(opts.maximized)`
- [x] Docs: `docs/FASE_86_MAXIMIZE.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_maximize_f86.py` + smoke F86
- [x] DEC-130 · bump **0.78.0**
- [x] Sin `FASE_86_APPROVED.md` · sin LIVE

## API de comandos

| id | action | label |
|----|--------|-------|
| `action.maximize_window` | `maximize_window` | Maximize window |
| `action.restore_from_maximize` | `restore_from_maximize` | Restore from Maximize |

Ambos: `safe=true`, `live=false`, keywords ES/EN. Operan sobre `focusedId` si no se pasa id. Registry vía `GET /api/commands`.

## Window manager

| Método | Comportamiento |
|--------|----------------|
| `maximize(id?, opts?)` | Guarda `preMax={x,y,w,h}`; llena workspace; clase `maximized`; `scheduleSave()` salvo `silent` |
| `restoreFromMaximize(id?, opts?)` | Aplica `preMax`; quita `maximized`; `scheduleSave()` salvo `silent` |
| `toggleMaximize(id?, opts?)` | Alterna maximize ↔ restoreFromMaximize |

`snapshotLayout()` serializa `maximized` y, si maximizada, persiste `preMax` como `x/y/w/h`. `open(opts.maximized)` restaura maximizada.

## UI

| Superficie | Binding |
|------------|---------|
| Command palette | `execute()` → `wm.maximize()` / `wm.restoreFromMaximize()` |
| Menú Inicio | Grupo Ventanas · `data-wm-action="maximize_window\|restore_from_maximize"` |
| Titlebar button | □ maximizar / ❐ restaurar |
| Titlebar dblclick | `toggleMaximize(id)` |
| Titlebar context | Maximize / Restore |

## Persistencia

Misma ruta F28: `scheduleSave()` → `_onLayoutChange(snapshotLayout())` → `PUT /api/layout` (incluye `windows.*.maximized`). Restore: `shell.mergeOpts` pasa `maximized` → `wm.open(..., {maximized})`.

## Notas técnicas

- JS: `static/js/wm.js`, `command_palette.js`, `shell.js`, `index.html`, `i18n.js`, `workbench.css`
- Python: `workbench/commands.py` (`_ACTION_COMMANDS`); `layout.py` valida `maximized: bool`
- Cascade/tile limpian estado maximized antes de recolocar

## Fuera de alcance

LIVE · auth WAN · Electron · certificado externo `FASE_86_APPROVED.md` · browser E2E · multi-monitor
