# Fase 87 — Broker Plugin Contract v1

**Estado:** ✅ **APROBADO_INTERNO** · certificado externo no emitido
**Versión:** 0.79.0 · **Base:** v0.78.0  
**DEC:** DEC-131 · **LIVE:** `LIVE_BLOCKED=True`

## Objetivo

Reemplazar el contrato implícito de factories externas por una spec versionada,
eliminar el retry ambiguo de `TypeError` y hacer cumplir en runtime que todo
plugin externo sea market-data/account read-only.

## DoD

- [x] `BrokerPluginSpec` frozen, API `"1"`, venue/capabilities validados.
- [x] Capabilities v1: `market_data`, `account_read`; ejecución prohibida.
- [x] `ReadOnlyBrokerPort` delega lecturas/lifecycle y bloquea submit/cancel.
- [x] Entry points v1; legacy v0 con warning y wrapper obligatorio.
- [x] Plugins sin shadow de builtins.
- [x] Registry inspecciona firma, rechaza opts incompatibles y llama una vez.
- [x] LIVE rechazado antes de factory.
- [x] Test kit offline/cooperativo con reporte frozen y validación de DTOs.
- [x] Tests adversariales + smoke F87.
- [x] Docs operativas + DEC-131 + bump 0.79.0.
- [x] Sin `FASE_87_APPROVED.md`; sin flip LIVE.

## Contrato y seguridad

La API pública vive en `quantlab.brokers.contracts.v1`; el test kit en
`quantlab.brokers.testing.contract_v1`. El test kit no ejecuta métodos de orden
del plugin y no pretende contener código hostil. La garantía de no ejecución
para callers normales está en el wrapper aplicado por `BrokerRegistry`.

No se introduce sandboxing. Instalar un paquete Python concede al plugin los
permisos del proceso; por eso sólo se admiten plugins confiables y cooperativos.

## QA

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance

Sandbox de plugins · ejecución de órdenes · flip LIVE · certificado externo
`FASE_87_APPROVED.md`.
