# Fase 81 — Custom Preset Delete

**Estado:** ✅ **APROBADO_INTERNO** (v0.73.0) — certificado externo `FASE_81_APPROVED.md` **NO** emitido  
**Base:** v0.72.0 · F80 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-125  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F81.md` · noche `INTERNAL_AUDIT_F19_F81_NIGHT.md`

## Objetivo

Borrar presets custom de sesión (`session/presets/{name}.json`) vía `DELETE /api/presets/{name}` y UI, sin permitir borrar built-ins `research` / `trading_paper` / `ops` — sin flip LIVE.

## DoD

- [x] `DELETE /api/presets/{name}` → borra solo custom
- [x] Built-ins `research|trading_paper|ops` → 400 fail-closed
- [x] Custom inexistente → 404
- [x] UI: botón × en filas custom (`data-preset-delete`)
- [x] Docs: `docs/FASE_81_PRESET_DELETE.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_preset_delete_f81.py` + smoke F81
- [x] DEC-125 · bump **0.73.0**
- [x] Sin `FASE_81_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/presets` | Built-in + custom (sin cambio) |
| POST | `/api/presets/apply` | Built-in o custom (sin cambio) |
| POST | `/api/presets/save` | Guarda custom (F80) |
| DELETE | `/api/presets/{name}` | Solo custom; built-ins protegidos |

### Respuesta delete

```json
{
  "ok": true,
  "kind": "preset_deleted",
  "preset": { "name": "my_desk", "custom": true, "path": "…" },
  "live_blocked": true,
  "live_routing": false,
  "research_safe": true
}
```

Built-in / nombre inválido → **400**. Custom no encontrado → **404**.

## Persistencia

```text
<data>/runtime/workbench/<session_id>/presets/<name>.json  → unlink
```

Built-ins viven en código (`presets.py`); no hay archivo que borrar.

## UI

| Control | Acción |
|---------|--------|
| `#custom-presets` filas `.custom-preset-row` | Apply (click nombre) |
| `[data-preset-delete]` | `confirm` → `DELETE /api/presets/{name}` |
| Built-in Research / Trading Paper / Ops | Sin botón delete |

Client: `QLApi.deletePreset(name)` · `deleteCustomPreset` en `shell.js`

## Notas técnicas

- Módulo: `workbench/presets.py` (`delete_custom_preset`)
- Handler: `handle_delete_presets` · `do_DELETE` en `server.py`
- Catálogo OpenAPI: `DELETE /api/presets/{name}`
- Path-safe: mismo `validate_preset_name` / `custom_preset_path` que F80

## Fuera de alcance

LIVE · auth WAN · Electron · rename UI · certificado externo `FASE_81_APPROVED.md` · browser E2E
