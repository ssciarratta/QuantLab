# FASE 95 — Diagnostics Snapshot Panel (read-only)

**Versión:** 0.87.0 · **DEC:** DEC-139 · **Fecha:** 2026-07-26
**Branch:** `cursor/modo-real-workbench-aafd` · **LIVE_BLOCKED:** True

---

## Objetivo

Dar a soporte/operación un único snapshot read-only del estado del Workbench
(versión, modo, salud, conexión, reconciliación) sin recorrer varios endpoints
ni paneles. Facilita adjuntar contexto a un reporte de incidente.

## Alcance

### API

`GET /api/diagnostics` (nuevo, tag `ops`): compone en un payload compacto:

- `version`, `phases_summary`, `live_blocked`, `live_routing` (false), `mode`,
  `real_alias`
- `session_id`, `connected_venue`, `md_provider`, `md_source`,
  `broker_connected`, `paper_kill_engaged`
- `health`: `status`, `checks_ok`, `checks_total` (resumen de
  `run_health_checks()`)
- `reconciliation`: `ok`, `status` (desde `check_paper_reconciliation()`)

No muta estado ni reconstruye archivos. Guard F55 sigue prohibiendo rutas LIVE.

### UI

- `static/js/panes/diagnostics.js`: badge OK/REVISAR, resumen `dl`, bloque JSON
  y botón "Copiar JSON" (clipboard).
- Cliente `QLApi.diagnostics()`; opener `shell.js`; start menu
  (`data-open="diagnostics"`); comando `open.diagnostics`; i18n
  `pane.diagnostics` (es/en + fallbacks).

## Fuera de alcance

- Acciones correctivas desde el pane (kill, rehydrate, connect): viven en sus
  paneles dedicados.

## DoD

- [x] `GET /api/diagnostics` read-only agregado
- [x] Pane read-only: única llamada `QLApi.diagnostics()`
- [x] Comando paleta + i18n es/en
- [x] Tests `test_diagnostics_f95.py` + smoke `check_f95_diagnostics`
- [x] Bump 0.87.0 · `PHASES_SUMMARY = "F19–F95 INTERNAL"`
- [x] Sin `FASE_95_APPROVED.md`; `LIVE_BLOCKED is True`
