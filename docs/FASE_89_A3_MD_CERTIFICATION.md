# Fase 89 — A3 Market Data Read-only Certification

Versión 0.81.0 · DEC-133 · `LIVE_BLOCKED=True`.

## Contrato

La certificación separa dos lanes que nunca se sustituyen entre sí:

- `fake`: obligatoria en CI/offline, determinista y sin red.
- `sandbox`: opt-in, exclusivamente pyRofex `simulation` y sin fallback a fake.

Los estados son `PASS`, `FAIL` y `SKIPPED_NOT_REQUESTED`. Un skip prueba
únicamente que la lane sandbox no fue solicitada; no equivale a certificación.

## Invariantes

1. El flujo sólo invoca connect, health, instrumentos, snapshot y, opcionalmente,
   cuenta/posiciones.
2. Un spy/write-bomb bloquea `place_order` y `cancel_order`; PASS exige
   `write_calls=0`.
3. DTOs numéricos deben ser finitos y timestamps de snapshots timezone-aware.
4. Sandbox exige `QUANTLAB_RUN_A3_SANDBOX_CERT=1`,
   `QUANTLAB_A3_MD_READONLY=1`, environment `simulation` y credenciales A3.
5. Production se rechaza antes de construir/conectar el backend.
6. La resolución sandbox usa `allow_fallback=False`.
7. El reporte sólo contiene conteos, latencias agregadas y códigos de issue:
   nunca credenciales, account IDs ni payloads raw.

## Estado de F89

La lane fake fue ejecutada localmente. La lane sandbox real queda
`SKIPPED_NOT_REQUESTED` mientras no exista un opt-in con credenciales de
simulation. F89 no afirma certificación A3 real ni habilita LIVE.

Operación: `docs/ops/A3_MD_CERTIFICATION.md`.
