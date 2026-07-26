# Fase 85 — Bring to Front / Send to Back

**Estado:** ✅ **APROBADO_INTERNO** (v0.77.0) — certificado externo `FASE_85_APPROVED.md` **NO** emitido  
**Base:** v0.76.0 · F84 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-129  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F85.md` · noche `INTERNAL_AUDIT_F19_F85_NIGHT.md`

## Objetivo

Comandos de z-order MDI: **Bring to Front** y **Send to Back** sobre la ventana enfocada (palette, menú Inicio, context menu titlebar); persistir / restaurar `z` en el layout — sin flip LIVE.

## DoD

- [x] Command palette: `action.bring_to_front` · `action.send_to_back`
- [x] Menú Inicio: grupo **Ventanas** con ambos botones (`data-wm-action`)
- [x] Context menu titlebar (right-click): Bring to Front / Send to Back
- [x] Titlebar dblclick → `bringToFront` (focus + raise z)
- [x] `wm.js`: `bringToFront(id)` / `sendToBack(id)` + `scheduleSave()`
- [x] Persist `z` (ya en `snapshotLayout`) + restore vía `mergeOpts` / `open(opts.z)`
- [x] Docs: `docs/FASE_85_ZORDER.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_zorder_f85.py` + smoke F85
- [x] DEC-129 · bump **0.77.0**
- [x] Sin `FASE_85_APPROVED.md` · sin LIVE

## API de comandos

| id | action | label |
|----|--------|-------|
| `action.bring_to_front` | `bring_to_front` | Bring to Front |
| `action.send_to_back` | `send_to_back` | Send to Back |

Ambos: `safe=true`, `live=false`, keywords ES/EN. Operan sobre `focusedId` si no se pasa id. Registry vía `GET /api/commands`.

## Window manager

| Método | Comportamiento |
|--------|----------------|
| `bringToFront(id?, opts?)` | Restaura si minimizada; `focus` (raise z); `scheduleSave()` salvo `silent` |
| `sendToBack(id?, opts?)` | Asigna `zIndex = max(1, minZ_siblings - 1)`; `scheduleSave()` salvo `silent` |

`snapshotLayout()` ya serializa `z` por ventana (F28). `open(opts.z)` restaura sin re-bump agresivo.

## UI

| Superficie | Binding |
|------------|---------|
| Command palette | `execute()` → `wm.bringToFront()` / `wm.sendToBack()` |
| Menú Inicio | Grupo Ventanas · `data-wm-action="bring_to_front\|send_to_back"` |
| Titlebar context | Right-click → menú Bring to Front / Send to Back |
| Titlebar dblclick | `bringToFront(id)` |

## Persistencia

Misma ruta F28: `scheduleSave()` → `_onLayoutChange(snapshotLayout())` → `PUT /api/layout` (incluye `windows.*.z`). Restore: `shell.mergeOpts` pasa `z` → `wm.open(..., {z})`.

## Notas técnicas

- JS: `static/js/wm.js`, `command_palette.js`, `shell.js`, `index.html`, `i18n.js`, `workbench.css`
- Python: `workbench/commands.py` (`_ACTION_COMMANDS`); layout `z` ya validado en `layout.py`

## Fuera de alcance

LIVE · auth WAN · Electron · certificado externo `FASE_85_APPROVED.md` · browser E2E · atajos de teclado dedicados (palette/menú/context suficientes)
