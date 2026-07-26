# Fase 84 — Cascade / Tile Windows

**Estado:** ✅ **APROBADO_INTERNO** (v0.76.0) — certificado externo `FASE_84_APPROVED.md` **NO** emitido  
**Base:** v0.75.0 · F83 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-128  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F84.md` · noche `INTERNAL_AUDIT_F19_F84_NIGHT.md`

## Objetivo

Comandos de layout MDI: **Cascade windows** y **Tile windows** desde command palette y menú Inicio; aplicar geometría pura, restaurar minimizadas, y persistir el layout — sin flip LIVE.

## DoD

- [x] Command palette: `action.cascade_windows` · `action.tile_windows`
- [x] Menú Inicio: grupo **Ventanas** con ambos botones (`data-wm-action`)
- [x] `wm.js`: `cascadeWindows()` / `tileWindows()` + `scheduleSave()`
- [x] Pure helpers `cascadeRects` / `tileRects` (JS) + espejo Python `window_layout`
- [x] Persist layout (posiciones/tamaños vía ruta F28)
- [x] Docs: `docs/FASE_84_CASCADE_TILE.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_cascade_tile_f84.py` + smoke F84
- [x] DEC-128 · bump **0.76.0**
- [x] Sin `FASE_84_APPROVED.md` · sin LIVE

## API de comandos

| id | action | label |
|----|--------|-------|
| `action.cascade_windows` | `cascade_windows` | Cascade windows |
| `action.tile_windows` | `tile_windows` | Tile windows |

Ambos: `safe=true`, `live=false`, keywords ES/EN. Registry vía `GET /api/commands`.

## Geometría pura

```text
cascadeRects(n, vw, vh, opts?) → [{x,y,w,h}, ...]
tileRects(n, vw, vh, opts?)    → [{x,y,w,h}, ...]
```

| Helper | Defaults | Comportamiento |
|--------|----------|----------------|
| Cascade | offset 28 · base (24,24) · size 420×320 | Diagonal; wrap a origen si sale del viewport |
| Tile | gap 4 · margin 4 | Grid near-square `cols=ceil(sqrt(n))` row-major |

Espejo Python: `quantlab.workbench.window_layout.cascade_rects` / `tile_rects`.

## Window manager

| Método | Comportamiento |
|--------|----------------|
| `cascadeWindows(opts?)` | Restaura minimizadas; aplica `cascadeRects`; focus última; `scheduleSave()` salvo `silent` |
| `tileWindows(opts?)` | Restaura minimizadas; aplica `tileRects`; focus última; `scheduleSave()` salvo `silent` |

## UI

| Superficie | Binding |
|------------|---------|
| Command palette | `execute()` → `wm.cascadeWindows()` / `wm.tileWindows()` |
| Menú Inicio | Grupo Ventanas · `data-wm-action="cascade_windows\|tile_windows"` |

## Persistencia

Misma ruta F28: `scheduleSave()` → `_onLayoutChange(snapshotLayout())` → `PUT /api/layout` (incluye `x/y/w/h` por ventana).

## Notas técnicas

- JS: `static/js/wm.js`, `command_palette.js`, `shell.js`, `index.html`, `i18n.js`
- Python: `workbench/commands.py` · `workbench/window_layout.py`

## Fuera de alcance

LIVE · auth WAN · Electron · certificado externo `FASE_84_APPROVED.md` · browser E2E · atajos de teclado dedicados (palette/menú suficientes) · snap entre ventanas
