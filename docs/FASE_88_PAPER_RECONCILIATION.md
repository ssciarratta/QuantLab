# Fase 88 — Paper Journal authoritative + Book reconciliation

Versión 0.80.0 · DEC-132 · `LIVE_BLOCKED=True`.

## Invariantes

1. `journal.jsonl` es la única secuencia autoritativa de fills PAPER y sólo se
   modifica por append + flush + `fsync`.
2. `book.json` es una proyección descartable y reconstruible mediante replay.
3. El commit de un fill ocurre en orden: preview → journal durable → book en
   memoria → book v2 atómico.
4. Nunca se persiste un book que no coincida exactamente, con `Decimal`, con el
   replay estricto del journal.
5. Corrupción, drift o una falla de persistencia posterior al append bloquean
   nuevos submits hasta check/rebuild y recarga.
6. No existe endpoint HTTP mutable de rebuild. El único rebuild es CLI offline.

## Formato book v2

```json
{
  "schema_version": 2,
  "book": {
    "initial_cash": "100000",
    "cash": "100000",
    "currency": "USD",
    "allow_short": false,
    "positions": {}
  },
  "journal_checkpoint": {
    "record_count": 0,
    "last_fill_id": null,
    "sha256": "e3b0..."
  }
}
```

El loader acepta el book flat legado. Sólo lo migra automáticamente a v2 si el
replay del journal produce exactamente el mismo estado. Una versión desconocida
o un book inválido falla cerrado.

## Lectura estricta

Cada línea debe terminar en newline y ser un objeto JSON con IDs y símbolo no
vacíos, `source="paper_broker"`, side buy/sell, timestamp con timezone y
quantity/price `Decimal` finitos. Se rechazan IDs de fill u orden duplicados,
líneas vacías, UTF-8/JSON inválido y registros truncados. El error incluye el
número de línea.

## Política de arranque

- Book v2 + checkpoint actual + replay exacto: `ok`.
- Book flat exacto: migración segura a v2 y `ok`.
- Journal válido por delante de un checkpoint v2 verificable:
  `rebuild_required` con `journal_ahead`.
- Book distinto, checkpoint por delante o digest incompatible:
  `rebuild_required`.
- Journal o book corrupto: `journal_corrupt` / `book_corrupt`.

F88 deliberadamente **no auto-recupera journal-ahead**. Aunque el checkpoint
demuestre un atraso limpio, el proceso queda bloqueado para que la operación sea
visible, respaldada y ejecutada offline con el CLI.

## Superficie

- `GET /api/paper/reconciliation`: status read-only.
- `scripts/reconcile_paper_session.py --session PATH --check`
- `scripts/reconcile_paper_session.py --session PATH --rebuild`

`--rebuild` valida todo el journal, crea `book.json.bak-<timestamp>`, reconstruye
y guarda v2 atómicamente. Nunca modifica el journal.

No se emite `FASE_88_APPROVED.md`; la aprobación de esta fase es INTERNAL.
