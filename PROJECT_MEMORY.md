# QuantLab Project Memory

Actualizado: 2026-07-26 · tip funcional F88 · versión 0.80.0.

- TESTER/PAPER operativos; REAL es alias de PAPER; LIVE routing sigue bloqueado.
- `LIVE_BLOCKED=True` y ningún cambio de F88 autoriza un flip.
- F17–F18 tienen certificación externa; F19–F87 están aprobadas INTERNAL.
- F88 implementa journal PAPER autoritativo y book reconstruible:
  - `journal.jsonl` append-only + fsync, lectura estricta.
  - `book.json` schema v2 atómico con checkpoint SHA-256.
  - commit order preview → journal → book → persist.
  - drift/corrupción bloquea submit.
  - rebuild únicamente por CLI offline, con backup; journal inmutable.
- Endpoint `/api/paper/reconciliation` es read-only.
- DEC vigente: DEC-132.
- No crear `FASE_88_APPROVED.md`; requiere Meta-Auditor externo.
