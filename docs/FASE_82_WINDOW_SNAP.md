# Fase 82 — Window Snap to Edges

**Estado:** ✅ **APROBADO_INTERNO** (v0.74.0) — certificado externo `FASE_82_APPROVED.md` **NO** emitido  
**Base:** v0.73.0 · F81 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-126  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F82.md` · noche `INTERNAL_AUDIT_F19_F82_NIGHT.md`

## Objetivo

Al soltar una ventana arrastrada en el window manager, alinearla a los bordes del viewport si la distancia al borde es **< 12px**, y persistir el layout — sin flip LIVE.

## DoD

- [x] `wm.js`: al `mouseup` de drag, `snapPosition(...)` con threshold 12px
- [x] Persist layout after snap (`scheduleSave()`)
- [x] Función pura `snapPosition(x,y,w,h,vw,vh,threshold)` en JS + espejo Python
- [x] Docs: `docs/FASE_82_WINDOW_SNAP.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_window_snap_f82.py` + smoke F82 (string snap en static/js)
- [x] DEC-126 · bump **0.74.0**
- [x] Sin `FASE_82_APPROVED.md` · sin LIVE

## Geometría

```text
snapPosition(x, y, w, h, vw, vh, threshold=12) → (x', y')
```

| Condición | Acción |
|-----------|--------|
| `x < threshold` | `x' = 0` (borde izquierdo) |
| `vw - (x+w) < threshold` | `x' = vw - w` (borde derecho; elif tras left) |
| `y < threshold` | `y' = 0` (borde superior) |
| `vh - (y+h) < threshold` | `y' = vh - h` (borde inferior; elif tras top) |

Left/top tienen prioridad sobre right/bottom cuando ambos gaps califican (ventanas casi full-bleed).

## Integración WM

| Evento | Acción |
|--------|--------|
| `_startDrag` → `mouseup` | Lee `left/top` + size + workspace size → `snapPosition` → escribe estilos → `scheduleSave()` |
| Resize `mouseup` | Sin snap (solo drag) |

Export: `QLSnapPosition` / `QLWindowManager.snapPosition` · constante `SNAP_THRESHOLD_PX = 12`.

## Persistencia

Misma ruta F28: `scheduleSave()` → `_onLayoutChange(snapshotLayout())` → `PUT /api/layout` (layout.json de sesión).

## Notas técnicas

- JS: `static/js/wm.js`
- Python mirror: `workbench/snap_position.py` (`snap_position`)
- Distancia estrictamente **menor** que threshold (`< 12`, no `<=`)

## Fuera de alcance

LIVE · auth WAN · Electron · snap entre ventanas · magnetic midlines · certificado externo `FASE_82_APPROVED.md` · browser E2E
