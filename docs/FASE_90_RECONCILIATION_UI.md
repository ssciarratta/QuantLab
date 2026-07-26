# Fase 90 — Paper Reconciliation Status Panel

**Estado:** implementada (v0.82.0) — certificado externo `FASE_90_APPROVED.md` **NO** emitido
Versión 0.82.0 · DEC-134 · `LIVE_BLOCKED=True`.

## Objetivo

Dar visibilidad operativa en el workbench al estado de reconciliación
journal/book de F88. La API `GET /api/paper/reconciliation` existía sin UI:
un drift o corrupción solo se descubría al fallar un submit o vía CLI.

## Entregas

- Panel SPA `Reconciliación` (grupo Sesión) **estrictamente read-only**:
  badge ok/status, `record_count`, checkpoint (record_count / last_fill_id /
  sha256), lista de issues y el comando CLI `rebuild_via` para recuperación.
- `QLApi.paperReconciliation()` → `GET /api/paper/reconciliation`.
- Auto-refresh opcional (10 s) con limpieza de intervalo al cerrar el panel.
- Command palette `open.reconciliation` + botón menú Inicio + i18n es/en.
- Suite `test_reconciliation_ui_f90.py` + smoke F90.

## Invariantes

1. La UI **no** dispara rebuild ni mutación alguna: sin POST/PUT/DELETE
   (verificado por test y smoke sobre el fuente del panel).
2. El único recovery mutable sigue siendo el CLI offline de F88
   (`scripts/reconcile_paper_session.py --rebuild`, con backup).
3. `LIVE_BLOCKED=True`; el panel no toca órdenes ni venues.

## Fuera de alcance

Rebuild vía HTTP · auto-recuperación · botón "releer sesión" (candidato F91) ·
badge en status bar · certificado externo `FASE_90_APPROVED.md` · browser E2E.
