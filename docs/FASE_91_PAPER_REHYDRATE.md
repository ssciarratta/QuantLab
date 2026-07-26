# Fase 91 — Paper Session Rehydrate post-rebuild

**Estado:** implementada (v0.83.0) — certificado externo `FASE_91_APPROVED.md` **NO** emitido
Versión 0.83.0 · DEC-135 · `LIVE_BLOCKED=True`.

## Objetivo

Cerrar el loop operativo de F88/F90: tras un `reconcile_paper_session.py
--rebuild` offline, el workbench quedaba con estado en memoria stale y la
única salida era reiniciar el proceso. F91 agrega un rehydrate explícito.

## Entregas

- `POST /api/paper/reconciliation/rehydrate`: teardown del runtime
  (runner/broker) + relectura de journal/book desde disco, igual que un
  reinicio de proceso. Retorna el ReconciliationReport resultante,
  `rehydrated=true`, `broker_connected` y `rebuild_via`.
- `WorkbenchState.rehydrate_session()` reusa `switch_session` (path ya
  auditado F46/F88) sobre el `session_id` actual.
- Botón "Releer sesión (post-rebuild)" en el panel Reconciliación (F90) con
  `confirm()` explícito; informa que hay que reconectar broker.
- Evento `rehydrate` agregado al allowlist del activity log (F41).
- Suite `test_paper_rehydrate_f91.py` + smoke F91.

## Invariantes

1. Rehydrate **nunca reconstruye archivos**: si el estado durable sigue
   inválido, el resultado queda igual de bloqueado que al boot
   (`rebuild_required` / `book_corrupt`). El único rebuild es el CLI offline.
2. El journal no se muta (verificado byte a byte en tests y smoke).
3. El teardown solo persiste el book en memoria si reconcilia exacto con el
   journal (política F52 existente); nunca pisa un rebuild válido.
4. Tras rehydrate el broker queda desconectado: reconexión explícita del
   operador (sin auto-reconnect).
5. `LIVE_BLOCKED=True`; POST-only en catálogo OpenAPI.

## Fuera de alcance

Rebuild vía HTTP · auto-reconnect de broker · auto-rehydrate al detectar
rebuild externo · certificado externo `FASE_91_APPROVED.md`.
