# Fase 83 — Minimize / Restore All

**Estado:** ✅ **APROBADO_INTERNO** (v0.75.0) — certificado externo `FASE_83_APPROVED.md` **NO** emitido  
**Base:** v0.74.0 · F82 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-127  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F83.md` · noche `INTERNAL_AUDIT_F19_F83_NIGHT.md`

## Objetivo

Comandos de ventana global: **Minimize all** y **Restore all windows** desde command palette y menú Inicio; persistir el flag `minimized` en el layout de sesión — sin flip LIVE.

## DoD

- [x] Command palette: `action.minimize_all` · `action.restore_all`
- [x] Menú Inicio: grupo **Ventanas** con ambos botones (`data-wm-action`)
- [x] `wm.js`: `minimizeAll()` / `restoreAll()` + `scheduleSave()`
- [x] Persist layout (`minimized` en `layout.json` vía ruta F28)
- [x] Docs: `docs/FASE_83_MINIMIZE_ALL.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_minimize_all_f83.py` + smoke F83 (commands API incluye nuevos comandos)
- [x] DEC-127 · bump **0.75.0**
- [x] Sin `FASE_83_APPROVED.md` · sin LIVE

## API de comandos

| id | action | label |
|----|--------|-------|
| `action.minimize_all` | `minimize_all` | Minimize all |
| `action.restore_all` | `restore_all` | Restore all windows |

Ambos: `safe=true`, `live=false`, keywords ES/EN. Registry vía `GET /api/commands`.

## Window manager

| Método | Comportamiento |
|--------|----------------|
| `minimizeAll(opts?)` | Minimiza todas las ventanas abiertas; `focusedId=null`; `scheduleSave()` salvo `silent` |
| `restoreAll(opts?)` | Restaura ventanas con clase `minimized` (vía `restore` → focus última); `scheduleSave()` salvo `silent` |

`snapshotLayout()` ya serializa `minimized` por ventana (F28).

## UI

| Superficie | Binding |
|------------|---------|
| Command palette | `execute()` → `wm.minimizeAll()` / `wm.restoreAll()` |
| Menú Inicio | Grupo Ventanas · `data-wm-action="minimize_all\|restore_all"` |

## Persistencia

Misma ruta F28: `scheduleSave()` → `_onLayoutChange(snapshotLayout())` → `PUT /api/layout` (incluye `windows.*.minimized`).

## Notas técnicas

- JS: `static/js/wm.js`, `command_palette.js`, `shell.js`, `index.html`, `i18n.js`
- Python: `workbench/commands.py` (`_ACTION_COMMANDS`)

## Fuera de alcance

LIVE · auth WAN · Electron · certificado externo `FASE_83_APPROVED.md` · browser E2E · atajos de teclado dedicados (palette/menú suficientes)
