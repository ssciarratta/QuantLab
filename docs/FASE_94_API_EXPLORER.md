# FASE 94 — API Explorer Panel (read-only)

**Versión:** 0.86.0 · **DEC:** DEC-138 · **Fecha:** 2026-07-26
**Branch:** `cursor/modo-real-workbench-aafd` · **LIVE_BLOCKED:** True

---

## Objetivo

Exponer el catálogo de la API del Workbench (OpenAPI 3, F55) en un pane
navegable read-only, para que el operador/investigador vea qué endpoints
existen sin abrir el JSON crudo ni herramientas externas.

## Alcance

### API

Reutiliza `GET /api/openapi.json` (F55). No agrega rutas ni muta nada.

### UI

- `static/js/panes/api_explorer.js`: tabla método/path/resumen/tags con filtro
  incremental (path, método, tag) y badge de conteo `mostradas/total`.
- Cliente `QLApi.openapi()`; opener en `shell.js`; start menu
  (`data-open="api_explorer"`); comando de paleta `open.api_explorer`; i18n
  `pane.api_explorer` (es/en + fallbacks).

## Fuera de alcance

- Ejecutar requests desde el pane (es solo un catálogo/visor).
- Editar/generar el schema.

## DoD

- [x] Pane read-only: única llamada `QLApi.openapi()`
- [x] Filtro incremental por path/método/tag
- [x] Comando paleta + i18n es/en
- [x] Tests `test_api_explorer_f94.py` + smoke `check_f94_api_explorer`
- [x] Bump 0.86.0 · `PHASES_SUMMARY = "F19–F94 INTERNAL"`
- [x] Sin `FASE_94_APPROVED.md`; `LIVE_BLOCKED is True`
