# Runbook — Paper reconciliation / rebuild

## Cuándo actuar

Actuar si `GET /api/paper/reconciliation` devuelve `ok=false`, si un submit
informa `reconciliation_required`, o después de una falla de disco al guardar
`book.json`.

## Procedimiento

1. Detener el workbench que usa la sesión. El CLI es offline y no coordina
   locks entre procesos.
2. Ejecutar check:

   ```bash
   uv run python scripts/reconcile_paper_session.py \
     --session data/runtime/workbench/SESSION_ID --check
   ```

3. Conservar el output JSON. Si el status es `journal_corrupt`, no ejecutar
   rebuild: preservar los archivos y escalar; el journal autoritativo no se
   trunca ni corrige automáticamente.
4. Si el journal es estricto y el status es `rebuild_required`, ejecutar:

   ```bash
   uv run python scripts/reconcile_paper_session.py \
     --session data/runtime/workbench/SESSION_ID --rebuild
   ```

5. Verificar que el resultado sea `ok=true`, que exista
   `book.json.bak-<timestamp>` y repetir `--check`.
6. Reiniciar el workbench. Un broker que ya quedó bloqueado no se habilita por
   cambios externos; requiere recarga de sesión/proceso.

## Interpretación

- `journal_ahead`: append durable completado, proyección/checkpoint atrasado.
- `book_ahead`: checkpoint declara registros que el journal no contiene.
- `book_mismatch`: estado económico distinto del replay exacto.
- `checkpoint_mismatch`: digest/último fill incompatible.
- `journal_corrupt`: JSONL, tipos, timezone, Decimal o duplicados inválidos.
- `book_corrupt`: envelope/schema/estado inválido.

## Prohibiciones

- No editar, truncar, ordenar ni deduplicar `journal.jsonl`.
- No copiar un book de otra sesión.
- No ejecutar rebuild por HTTP.
- No desactivar `LIVE_BLOCKED`.
- No ejecutar el CLI en paralelo con submits.
