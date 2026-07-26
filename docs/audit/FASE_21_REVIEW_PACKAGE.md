# Review Package — FASE 21 Lab Panels

**Fecha:** 2026-07-26  
**Versión código:** 0.13.0  
**Tipo:** Review Package **INTERNAL** (Meta-Auditor INTERNO Zero-Trust)  
**Implementación:** commit `c397ffc` (bump lock `0de4211`)  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F21.md`  
**Veredicto INTERNAL:** `docs/audit/INTERNAL_AUDIT_F21.md`  
**Implementation report:** `docs/audit/FASE_21_IMPLEMENTATION_REPORT.md`

> **Aclaración:** este paquete **NO** constituye `FASE_21_APPROVED` formal del Meta-Auditor **externo**.  
> Es evidencia + Lista A/B para auditoría interna y para un futuro Review Package externo.

---

## Architecture Review (resumen)

**Opción elegida:** adapters thin en `lab_services.py` sobre módulos research existentes + JSON `/api/lab/*` + paneles SPA MDI (DEC-061/062).  
**Alternativa descartada:** reimplementar backtest/optimizer en JS o exponer CLIs vía shell (superficie / seguridad).  
**Criterio:** mouse-first sobre demos sintéticos; `live_routing: false`; export HB path-safe; sin chat; sin flip LIVE.

---

## Lista A — Entregables a auditar

| ID | Entregable | Path |
|----|------------|------|
| A1 | Lab adapters thin | `src/quantlab/workbench/lab_services.py` |
| A2 | Handlers `/api/lab/*` | `src/quantlab/workbench/api.py` |
| A3 | Rutas HTTP lab | `src/quantlab/workbench/server.py` |
| A4 | Cliente API lab | `workbench/static/js/api.js` |
| A5 | Helpers + 9 paneles lab | `static/js/panes/lab_common.js` + panes lab |
| A6 | Shell menú Laboratorio | `static/js/shell.js`, `static/index.html` |
| A7 | LIVE gate intacto | `src/quantlab/execution/live_gate.py` (`LIVE_BLOCKED=True`) |
| A8 | Spec DoD F21 | `docs/FASE_21_LAB_PANELS.md` |
| A9 | DEC-062 (+ DEC-061 prereq) | `learning/decisiones.txt` |
| A10 | Suite unit lab | `tests/unit/workbench/test_lab_api.py` (+ suite F20) |
| A11 | Implementation report | `docs/audit/FASE_21_IMPLEMENTATION_REPORT.md` |
| A12 | Version 0.13.0 | `pyproject.toml`, `quantlab/__init__.py` |

---

## Lista B — Evidencia QA

```
uv run mypy --strict src/quantlab     → Success (143 files)
uv run ruff check src/quantlab        → All checks passed
uv run pytest tests/unit/workbench -q → 23 passed
uv run quantlab-health                → ok=true, live_blocked=true,
                                         operating_mode=tester, v0.13.0,
                                         venues=['a3','binance','paper']
```

Probes adicionales:

- `LIVE_BLOCKED is True`
- POST `/api/mode` `live` → 400
- `quantlab-workbench --mode live` → exit 2
- POST `/api/lab/export-hb` con `path` → 400
- Export payload `live_routing: false`
- Capabilities incluyen backtest/scanner/optimize/… + strategies

---

## Invariantes

- LIVE order routing: **BLOQUEADO**
- Workbench bind default: **127.0.0.1**
- Lab demos: **sintéticos / tmp sesión** (sin credenciales)
- Export HB: **sandbox + live_routing false**
- Flip `LIVE_BLOCKED`: **NO ejecutado**
- Sin certificado externo hasta APROBADO Meta-Auditor externo
- Chat (F22): **fuera de alcance**

---

## Pedido al Meta-Auditor externo (futuro)

1. Revisar Lista A+B + `INTERNAL_AUDIT_F21.md`.  
2. Emitir **APROBADO** / observaciones.  
3. Solo con APROBADO → generar `docs/audit/FASE_21_APPROVED.md`.
