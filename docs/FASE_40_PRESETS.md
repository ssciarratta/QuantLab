# Fase 40 — Workspace Presets

**Estado:** ✅ **APROBADO_INTERNO** (v0.32.0) — certificado externo `FASE_40_APPROVED.md` **NO** emitido  
**Base:** v0.31.0 · F39 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-084  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F40.md` · noche `INTERNAL_AUDIT_F19_F40_NIGHT.md`

## Objetivo
Presets de espacio de trabajo que reescriben `layout.json` con un conjunto fijo de paneles MDI (research / trading paper / ops), accesibles desde el menú Inicio.

## DoD
- [x] Presets: `research`, `trading_paper`, `ops`
- [x] API `GET /api/presets` + `POST /api/presets/apply` `{name}`
- [x] Apply actualiza `layout.json` (reemplazo total de ventanas)
- [x] UI: Inicio → Espacios de trabajo / presets
- [x] Docs: `docs/FASE_40_PRESETS.md` + IMPLEMENTATION_REPORT
- [x] Tests + QA
- [x] DEC-084 · bump **0.32.0**
- [x] Sin `FASE_40_APPROVED.md` · sin LIVE

## Presets

| name | label | Ventanas |
|------|-------|----------|
| `research` | Research | Health + Backtest + Reports + Chat |
| `trading_paper` | Trading Paper | Market + Blotter + Positions + Session + Risk |
| `ops` | Ops | Health + Settings + Docs + Catalog |

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/presets` | Catálogo: name, label, description, window_ids |
| POST | `/api/presets/apply` | body `{ "name": "research" }` → escribe layout |

Respuesta incluye: `live_blocked`, `live_routing:false`, `research_safe:true`, `layout`.

### Body apply

```json
{ "name": "research" }
```

Nombre desconocido → 400 fail-closed.

## UI

- Menú Inicio → grupo **Espacios de trabajo**
- Botones Research / Trading Paper / Ops
- Al aplicar: cierra ventanas abiertas, abre las del preset con geometría del layout guardado
- Client: `QLApi.getPresets` / `QLApi.applyPreset`

## Notas técnicas
- Módulo: `workbench/presets.py`
- Persistencia: reutiliza `layout.save_layout` (F28)
- Apply = reemplazo total de `windows` (no merge)

## Fuera de alcance
LIVE · auth WAN · Electron · certificado externo `FASE_40_APPROVED.md` · presets custom usuario · browser E2E
