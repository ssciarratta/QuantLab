# FASE 93 — Venues / Broker Registry Panel (read-only)

**Versión:** 0.85.0 · **DEC:** DEC-137 · **Fecha:** 2026-07-26
**Branch:** `cursor/modo-real-workbench-aafd` · **LIVE_BLOCKED:** True

---

## Objetivo

Dar visibilidad operativa al registro de brokers (F19 registry + F24/F87
plugins) desde el Workbench, de forma **estrictamente read-only**: qué venues
están registrados, cuáles vienen de plugins externos (contrato v1, siempre
detrás de `ReadOnlyBrokerPort`), cuál está conectado y bajo qué proveedor de MD.

## Alcance

### API

`GET /api/venues` (existente desde F19/F24) se enriquece con:

- `connected_venue` · `md_provider` · `mode` · `live_blocked`
- `plugin_contract`: `api_version` ("1"), `allowed_capabilities`
  (`account_read`, `market_data`), `read_only_wrapper` (`ReadOnlyBrokerPort`),
  `execution` (`blocked`)

Sin rutas nuevas; sin mutaciones.

### UI

- `static/js/panes/venues.js`: badge de conteo, conexión actual, lista de
  venues con tags `[builtin]` / `[plugin · read-only]` / `[conectado]`, y
  resumen del contrato de plugins v1.
- Start menu (`data-open="venues"`), opener en `shell.js`, comando de paleta
  `open.venues`, i18n `pane.venues` (es/en + fallbacks).

## Fuera de alcance

- Conectar/desconectar brokers desde este pane (existe flujo aparte).
- Cargar/descargar plugins en runtime.
- Cualquier capacidad de ejecución (prohibida por contrato v1 y `LIVE_BLOCKED`).

## DoD

- [x] Payload enriquecido con contrato v1 y estado de conexión
- [x] Pane read-only: única llamada `QLApi.venues()`
- [x] Comando paleta + i18n es/en
- [x] Tests `test_venues_panel_f93.py` (payload, comando, estáticos, read-only)
- [x] Smoke `check_f93_venues_panel`
- [x] Bump 0.85.0 · `PHASES_SUMMARY = "F19–F93 INTERNAL"`
- [x] Sin `FASE_93_APPROVED.md`; `LIVE_BLOCKED is True`
