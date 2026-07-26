# Review Package — FASE 25 Ops Desk (1-click + hardening)

**Fecha:** 2026-07-26  
**Versión código (impl F25):** 0.17.0  
**Tipo:** Review Package **INTERNAL** (Meta-Auditor INTERNO Zero-Trust)  
**Implementación:** commit `21fe144`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F25.md`  
**Veredicto INTERNAL:** `docs/audit/INTERNAL_AUDIT_F25.md`  
**Implementation report:** `docs/audit/FASE_25_IMPLEMENTATION_REPORT.md`

> **Aclaración:** este paquete **NO** constituye `FASE_25_APPROVED` formal del Meta-Auditor **externo**.  
> Es evidencia + Lista A/B para auditoría interna y para un futuro Review Package externo.

---

## Architecture Review (resumen)

**Opción elegida:** launcher bash + `.desktop` 1-click; gate explícito `--allow-non-loopback`; charset fail-closed `experiment_id`; slippage paper adverso; panel Riesgo read-only (DEC-069).  
**Alternativa descartada:** Electron / auth WAN / flip LIVE / bind abierto sin flag.  
**Criterio:** ops desk research-safe — default loopback; M1/M2 heredados cerrados; **nunca** flip LIVE.

---

## Lista A — Entregables a auditar

| ID | Entregable | Path |
|----|------------|------|
| A1 | Launcher 1-click | `scripts/launch_workbench.sh` |
| A2 | Desktop entry | `packaging/quantlab-workbench.desktop` |
| A3 | Ops 1-click doc | `docs/ops/WORKBENCH_1CLICK.md` |
| A4 | Non-loopback gate + slip CLI | `src/quantlab/workbench/launch.py` |
| A5 | `validate_experiment_id` | `src/quantlab/workbench/lab_services.py` |
| A6 | Paper slippage adverso | `src/quantlab/brokers/paper/broker.py` |
| A7 | `GET /api/risk` + connect slip | `src/quantlab/workbench/api.py` + `server.py` |
| A8 | Panel Riesgo + banner session | `static/js/panes/risk.js` · `shell.js` · `index.html` |
| A9 | LIVE gate intacto | `src/quantlab/execution/live_gate.py` |
| A10 | Spec DoD F25 | `docs/FASE_25_OPS_DESK.md` |
| A11 | DEC-069 | `learning/decisiones.txt` |
| A12 | Suite unit F25 | `test_launch_non_loopback.py`, `test_experiment_id_charset.py`, `test_paper_slippage_bps.py`, `test_api_risk.py` |
| A13 | Smoke F25 | `scripts/internal_audit_smoke.py` |
| A14 | Implementation report | `docs/audit/FASE_25_IMPLEMENTATION_REPORT.md` |
| A15 | Version 0.17.0 | `pyproject.toml` @ `21fe144` |

---

## Lista B — Evidencia QA

```
uv run mypy --strict src/quantlab     → Success (156 files)
uv run ruff check src/quantlab        → All checks passed
uv run pytest -q                      → 552 passed
uv run quantlab-health                → ok=true, live_blocked=true, version=0.17.0
uv run python scripts/internal_audit_smoke.py → PASS (11 checks)
```

Probes adicionales:

- `LIVE_BLOCKED is True`
- Non-loopback sin flag → exit 2; con flag → WARNING
- `experiment_id` traversal / dots → ValidationError
- Slip BUY peor / SELL peor
- `handle_get_risk` → limits + session + `live_blocked`
- Banner `session_id` + menú Inicio → Riesgo

---

## Remediación / hardening INTERNAL

| ID | Severidad | Fix |
|----|-----------|-----|
| — | CRITICAL/HIGH | **Ninguno abierto** (M1/M2 previos cerrados por impl F25) |
| H-cov | hardening | Test allow+warning; API risk; smoke ops desk; DEC-069 |

---

## Invariantes

- LIVE order routing: **BLOQUEADO**
- Workbench bind default: **127.0.0.1**
- Non-loopback: **flag explícito** + warning
- `experiment_id`: charset fail-closed
- Paper slip: adverso; default `0`
- Flip `LIVE_BLOCKED`: **NO ejecutado**
- Sin certificado externo hasta APROBADO Meta-Auditor externo

---

## Pedido al Meta-Auditor externo (futuro)

1. Revisar Lista A+B + `INTERNAL_AUDIT_F25.md` + arco F23–F25.  
2. Emitir **APROBADO** / observaciones.  
3. Solo con APROBADO → generar `docs/audit/FASE_25_APPROVED.md`.
