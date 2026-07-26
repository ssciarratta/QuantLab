# Fase 35 — Command Palette + Keyboard Shortcuts

**Estado:** ✅ **APROBADO_INTERNO** (v0.27.0) — certificado externo `FASE_35_APPROVED.md` **NO** emitido  
**Base:** v0.26.0 · F34 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-079  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F35.md` · noche `INTERNAL_AUDIT_F19_F35_NIGHT.md`

## Objetivo
UX Windows-like: command palette (`Ctrl+K` / `Ctrl+Shift+P`) para buscar y abrir cualquier panel/ventana; atajos de teclado `Ctrl+1..9`, `Esc`, `Ctrl+W`; API `GET /api/commands` con paneles + acciones seguras (health refresh — **sin LIVE**).

## DoD
- [x] Command palette JS (Ctrl+K / Ctrl+Shift+P)
- [x] Shortcuts: Ctrl+1..9 open panes · Esc close palette · Ctrl+W close focused
- [x] API `GET /api/commands` — paneles + acciones seguras
- [x] Docs: `docs/FASE_35_COMMAND_PALETTE.md` + IMPLEMENTATION_REPORT
- [x] Tests API commands + smoke; JS vía presencia API/static
- [x] DEC-079 · bump **0.27.0**

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/commands` | lista comandos (`kind`: pane\|action) + shortcuts |

Respuesta incluye: `commands[]`, `pane_shortcut_order`, `palette_shortcuts`, `live_blocked`, `live_routing:false`, `research_safe:true`.

Acciones seguras: `health_refresh`, `close_focused`.  
**No** incluye flip LIVE / place_order / set_live.

## Atajos

| Shortcut | Acción |
|----------|--------|
| Ctrl+K · Ctrl+Shift+P | Toggle command palette |
| Esc | Cerrar palette |
| Ctrl+1..9 | Abrir paneles (health…risk) |
| Ctrl+W | Cerrar ventana enfocada |

Orden Ctrl+1..9: health, market, universe, catalog, blotter, journal, paper_session, positions, risk.

## UI

- Overlay central searchable (fuzzy por label / id / keywords)
- ↑↓ navegar · Enter ejecutar · click ejecutar
- WM: `focusedId` + `closeFocused()`

## Notas técnicas
- Registry en `workbench/commands.py` (fuente de verdad API + UI)
- Client-side execution vía `openers` del shell (sin mutaciones LIVE)
- JS tested vía `/` + static presence (no browser E2E)

## Fuera de alcance
LIVE · auth WAN · Electron · certificado externo `FASE_35_APPROVED.md` · browser E2E
