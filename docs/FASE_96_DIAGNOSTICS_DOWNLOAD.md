# FASE 96 — Diagnostics Download (support snapshot)

**Versión:** 0.88.0 · **DEC:** DEC-140 · **Fecha:** 2026-07-26
**Branch:** `cursor/modo-real-workbench-aafd` · **LIVE_BLOCKED:** True

---

## Objetivo

Permitir descargar el snapshot de diagnóstico (F95) como archivo JSON, para
adjuntarlo directamente a un reporte de incidente sin copiar/pegar del pane.

## Alcance

### API

`GET /api/diagnostics.json` (nuevo, tag `ops`): reutiliza
`handle_get_diagnostics` (read-only), serializa a JSON indentado y lo devuelve
como descarga adjunta (`Content-Disposition: attachment`). El nombre de archivo
se sanea a partir del `session_id` (`quantlab-diagnostics-<session>.json`).

### UI

- Botón "Descargar" en `static/js/panes/diagnostics.js` (ancla `download` a
  `/api/diagnostics.json`).
- Helper `QLApi.diagnosticsDownloadUrl()` en `api.js`.

## Fuera de alcance

- Bundles multi-archivo (zip); esto es solo el snapshot JSON.

## DoD

- [x] `GET /api/diagnostics.json` descarga adjunta read-only
- [x] Nombre de archivo saneado por `session_id`
- [x] Botón de descarga en el pane + helper de URL
- [x] Tests `test_diagnostics_download_f96.py` + smoke `check_f96_diagnostics_download`
- [x] Bump 0.88.0 · `PHASES_SUMMARY = "F19–F96 INTERNAL"`
- [x] Sin `FASE_96_APPROVED.md`; `LIVE_BLOCKED is True`
