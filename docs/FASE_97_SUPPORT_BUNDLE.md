# FASE 97 — Support Bundle ZIP (read-only)

**Versión:** 0.89.0 · **DEC:** DEC-141 · **Fecha:** 2026-07-26
**Branch:** `cursor/modo-real-workbench-aafd` · **LIVE_BLOCKED:** True

---

## Objetivo

Empaquetar en un único ZIP los snapshots read-only ya existentes (F93–F96)
para adjuntar a un reporte de incidente, sin exponer journal/book ni credenciales.

## Alcance

### API

`GET /api/support-bundle.zip` (nuevo, tag `ops`): ZIP en memoria con:

- `README.txt` (versión, session_id, live_blocked, inventario)
- `diagnostics.json` (F95)
- `about.json`
- `openapi.json` (F55/F94)
- `venues.json` (F93)
- `reconciliation.json` (F90; fail-soft si no disponible)

Nombre: `quantlab-support-<session_id>.zip` (saneado).

### UI

- Botón "Support ZIP" en pane Diagnostics.
- Helper `QLApi.supportBundleUrl()`.

## Fuera de alcance

- Incluir journal/book, fills, backups o settings con secretos.
- Upload remoto del bundle.

## DoD

- [x] ZIP read-only con miembros documentados
- [x] Sin journal/book en el ZIP
- [x] Botón en pane + helper URL
- [x] Tests + smoke F97
- [x] Bump 0.89.0 · `PHASES_SUMMARY = "F19–F97 INTERNAL"`
- [x] Sin `FASE_97_APPROVED.md`; `LIVE_BLOCKED is True`
