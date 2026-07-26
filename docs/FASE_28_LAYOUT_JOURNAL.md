# Fase 28 — Workbench Layout Persistence + Journal Viewer

**Estado:** ✅ **APROBADO_INTERNO** (v0.20.0) — certificado externo `FASE_28_APPROVED.md` **NO** emitido  
**Base:** v0.19.0 · F27 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-072  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F28.md` · noche `INTERNAL_AUDIT_F19_F28_NIGHT.md`

## Objetivo
Persistir geometría del window manager MDI por sesión (`layout.json`) y exponer un panel Journal con tabla de fills paper + export CSV local.

## DoD
- [x] `src/quantlab/workbench/layout.py` — save/load posiciones/tamaños → session `layout.json`
- [x] API: `GET` / `PUT` `/api/layout`
- [x] JS `wm.js`: debounce save al mover/resize; restore al boot
- [x] Panel Journal: `GET /api/paper/fills` + UI `panes/journal.js` (tabla + export CSV client-side)
- [x] Docs: `docs/FASE_28_LAYOUT_JOURNAL.md` + IMPLEMENTATION_REPORT
- [x] Tests layout save/load + API
- [x] DEC-072 · bump **0.20.0**

## Layout schema

```json
{
  "version": 1,
  "windows": {
    "health": { "x": 24, "y": 20, "w": 440, "h": 360, "minimized": false, "z": 11 }
  }
}
```

- Path: `<session_root>/layout.json`
- Validación fail-closed: window ids `[A-Za-z][A-Za-z0-9_-]{0,63}`, rangos px acotados, máx. 64 ventanas
- Escritura atómica (tmp + replace)

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/layout` | layout actual (vacío canónico si no hay archivo) |
| PUT | `/api/layout` | body = layout o `{ "layout": {...} }` |
| GET | `/api/paper/fills` | ya existía — fuente del Journal |

## UI

- `wm.js`: `snapshotLayout` / `scheduleSave` (debounce 400 ms) en drag/resize/minimize/close
- `shell.js`: carga layout al boot y aplica geometría al abrir paneles
- Inicio → **Journal**: tabla fills + Export CSV (Blob local, sin endpoint extra)

## Notas técnicas
- Sin flip LIVE · sin place_order venue
- Export CSV es 100% client-side (no escribe en `exports/` del servidor)

## Fuera de alcance
LIVE · auth WAN · sync layout multi-proceso · server-side CSV export
