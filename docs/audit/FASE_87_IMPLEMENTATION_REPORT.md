# FASE 87 — Implementation Report (Broker Plugin Contract v1)

**Fecha:** 2026-07-26  
**Versión:** 0.79.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F86 v0.78.0  
**Impl SHA:** este commit  
**Alcance:** contrato externo MD/account read-only — **sin flip LIVE**

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Spec pública versionada | `brokers/contracts/v1.py` |
| D2 | Wrapper read-only obligatorio | `brokers/read_only.py` · `registry.py` |
| D3 | Loader v1 + compat legacy warning | `brokers/plugins.py` |
| D4 | Factory signature bind + one-shot invocation | `brokers/registry.py` |
| D5 | Test kit cooperativo | `brokers/testing/contract_v1.py` |
| D6 | Suite adversarial | `tests/unit/brokers/test_plugin_contract_v1.py` |
| D7 | Operación/spec | `docs/ops/BROKER_PLUGIN_CONTRACT_V1.md` · `docs/FASE_87_PLUGIN_CONTRACT.md` |
| D8 | DEC-131 + bump | `learning/decisiones.txt` · 0.79.0 |
| D9 | Smoke F87 | `scripts/internal_audit_smoke.py` |

## Invariantes

- `LIVE_BLOCKED is True`; LIVE se rechaza antes de factory.
- Plugins externos sólo exponen market data/account read mediante wrapper.
- Registry no captura `TypeError` producido dentro de una factory.
- Factory plugin invocada exactamente una vez por `create`.
- Sin shadow de builtins.
- El test kit no es sandbox y no llama ejecución del objeto plugin.
- Sin `FASE_87_APPROVED.md`.

## QA requerida

```text
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```
