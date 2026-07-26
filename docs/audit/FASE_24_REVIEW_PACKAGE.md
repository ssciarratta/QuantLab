# Review Package — FASE 24 Venue plugins + MD read-only

**Fecha:** 2026-07-26  
**Versión código (impl F24):** 0.16.0  
**Tipo:** Review Package **INTERNAL** (Meta-Auditor INTERNO Zero-Trust)  
**Implementación:** commit `c846e81`  
**Remediación H1:** commit `25f7ba1`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F24.md`  
**Veredicto INTERNAL:** `docs/audit/INTERNAL_AUDIT_F24.md`  
**Implementation report:** `docs/audit/FASE_24_IMPLEMENTATION_REPORT.md`

> **Aclaración:** este paquete **NO** constituye `FASE_24_APPROVED` formal del Meta-Auditor **externo**.  
> Es evidencia + Lista A/B para auditoría interna y para un futuro Review Package externo.

---

## Architecture Review (resumen)

**Opción elegida:** entry points `quantlab.brokers` + A3 MD env opt-in fail-closed + generics CSV/REST MD-only (DEC-067/068).  
**Alternativa descartada:** SDKs venue hardcodeados en core / submit A3 vía PyRofex / flip LIVE.  
**Criterio:** research-safe — plugins no tumban registry; no shadow builtins; MD env no habilita órdenes; submit/cancel gated; **nunca** flip LIVE.

---

## Lista A — Entregables a auditar

| ID | Entregable | Path |
|----|------------|------|
| A1 | Entry-point loader | `src/quantlab/brokers/plugins.py` |
| A2 | Registry + builtins + plugins | `src/quantlab/brokers/registry.py` |
| A3 | A3 MD resolve fake\|env | `src/quantlab/brokers/a3/md_backend.py` |
| A4 | A3BrokerPort MD-only gated | `src/quantlab/brokers/a3/adapter_port.py` |
| A5 | GenericCsvMdBroker | `src/quantlab/brokers/generic/csv_md.py` |
| A6 | FakeRestMdBroker skeleton | `src/quantlab/brokers/generic/rest_skeleton.py` |
| A7 | Workbench md_provider / connect | `src/quantlab/workbench/api.py` + Market UI |
| A8 | LIVE gate intacto | `src/quantlab/execution/live_gate.py` |
| A9 | Spec DoD F24 | `docs/FASE_24_VENUE_MD_PLUGINS.md` |
| A10 | Ops plugins | `docs/ops/BROKER_PLUGINS.md` |
| A11 | DEC-067 / DEC-068 | `learning/decisiones.txt` |
| A12 | Suite unit plugins/a3/generic/API | `tests/unit/brokers/test_plugins.py`, `test_a3_md_readonly_fallback.py`, `test_generic_rest_csv.py`, `tests/unit/workbench/test_api_md_provider.py` |
| A13 | Implementation report | `docs/audit/FASE_24_IMPLEMENTATION_REPORT.md` |
| A14 | Version 0.16.0 | `pyproject.toml` @ `c846e81` |

---

## Lista B — Evidencia QA

```
uv run mypy --strict src/quantlab     → Success
uv run ruff check src/quantlab        → All checks passed
uv run pytest -q                      → 516 passed
uv run quantlab-health                → ok=true, live_blocked=true, version=0.16.0
uv run python scripts/internal_audit_smoke.py → PASS
```

Probes adicionales:

- `LIVE_BLOCKED is True`
- Plugin load failure → no crash; shadow `a3` → refused (remediación H1)
- `md_source=env` sin flag → fake + `md_fallback`
- A3 / generic_csv / generic_rest `submit`/`cancel` → BLOQUEADO
- GET `/api/health` / `/api/session`: `md_provider`, `plugin_venues`, `venues`

---

## Remediación INTERNAL (CRITICAL/HIGH)

| ID | Severidad | Fix |
|----|-----------|-----|
| H1 | HIGH | Plugins no pueden sombrear venues ya registrados (`has_venue` + warning + `ValidationError` en `register(..., from_plugin=True)`) |

---

## Invariantes

- LIVE order routing: **BLOQUEADO**
- Workbench bind default: **127.0.0.1**
- A3 MD env: **opt-in** + fallback fake; **no** submit venue
- Plugins: **fail-soft** load; **no shadow** builtins
- Flip `LIVE_BLOCKED`: **NO ejecutado**
- Sin certificado externo hasta APROBADO Meta-Auditor externo

---

## Pedido al Meta-Auditor externo (futuro)

1. Revisar Lista A+B + `INTERNAL_AUDIT_F24.md` + remediación H1.  
2. Emitir **APROBADO** / observaciones.  
3. Solo con APROBADO → generar `docs/audit/FASE_24_APPROVED.md`.
