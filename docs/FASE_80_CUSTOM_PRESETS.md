# Fase 80 — Custom Preset Save

**Estado:** ✅ **APROBADO_INTERNO** (v0.72.0) — certificado externo `FASE_80_APPROVED.md` **NO** emitido  
**Base:** v0.71.0 · F79 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-124  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F80.md` · noche `INTERNAL_AUDIT_F19_F80_NIGHT.md`

## Objetivo

Guardar el `layout.json` actual de la sesión como preset nombrado bajo `session/presets/{name}.json`, listarlo junto a los built-in, y poder re-aplicarlo — sin flip LIVE.

## DoD

- [x] `POST /api/presets/save` `{name}` → `presets/{name}.json`
- [x] `GET /api/presets` incluye custom (`custom: true`)
- [x] `POST /api/presets/apply` funciona para custom
- [x] UI: Inicio → **Guardar espacio actual…** + lista custom dinámica
- [x] Validación fail-closed (path-safe; no shadow `research|trading_paper|ops`)
- [x] Session ZIP incluye dir `presets/`
- [x] Docs: `docs/FASE_80_CUSTOM_PRESETS.md` + IMPLEMENTATION_REPORT
- [x] Suite `test_custom_presets_f80.py` + smoke F80
- [x] DEC-124 · bump **0.72.0**
- [x] Sin `FASE_80_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/presets` | Built-in + custom de sesión |
| POST | `/api/presets/apply` | `{ "name": "…" }` built-in o custom |
| POST | `/api/presets/save` | `{ "name": "my_desk" }` → copia layout actual |

### Body save

```json
{ "name": "my_desk" }
```

Opcional: `label`, `description`.

Nombre inválido / built-in / traversal → 400 fail-closed.

### Catálogo

Cada item incluye `custom: true|false`, `window_ids`, `window_count`.  
Respuesta agrega `builtin_count`, `custom_count`.

## Persistencia

```text
<data>/runtime/workbench/<session_id>/presets/<name>.json
```

Shape:

```json
{
  "version": 1,
  "name": "my_desk",
  "label": "my_desk",
  "description": "Custom preset",
  "custom": true,
  "windows": { "health": { "x": 24, "y": 20, "w": 420, "h": 340 } }
}
```

## UI

| Control | Acción |
|---------|--------|
| `#btn-preset-save` | `prompt` nombre → `POST /api/presets/save` |
| `#custom-presets` | Botones dinámicos `data-preset` para custom |
| Built-in Research / Trading Paper / Ops | Sin cambios (F40) |

Client: `QLApi.savePreset(name)` · `QLApi.getPresets` / `applyPreset`

## Notas técnicas

- Módulo: `workbench/presets.py` (`save_custom_preset`, `list_custom_presets`)
- Max 64 custom por sesión
- Apply = reemplazo total de `windows` (igual F40)
- Export ZIP sesión incluye `presets/`

## Fuera de alcance

LIVE · auth WAN · Electron · delete/rename UI · certificado externo `FASE_80_APPROVED.md` · browser E2E
