# Review Package — FASE 20 Workbench

**Fecha:** 2026-07-26  
**Versión código:** 0.12.0  
**Tipo:** Review Package **INTERNAL** (Meta-Auditor INTERNO Zero-Trust)  
**Implementación:** commit `cacf8e6`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F20.md`  
**Veredicto INTERNAL:** `docs/audit/INTERNAL_AUDIT_F20.md`  
**Implementation report:** `docs/audit/FASE_20_IMPLEMENTATION_REPORT.md`

> **Aclaración:** este paquete **NO** constituye `FASE_20_APPROVED` formal del Meta-Auditor **externo**.  
> Es evidencia + Lista A/B para auditoría interna y para un futuro Review Package externo.

---

## Architecture Review (resumen)

**Opción elegida:** `stdlib http.server` + SPA estática con window-manager (DEC-061); sin deps UI nuevas.  
**Alternativa descartada:** Electron / FastAPI+React (peso, superficie de ataque, deps).  
**Criterio:** 1-click local loopback; órdenes solo vía `PaperBroker`; LIVE fail-closed; UI ES con 3 paneles shell.

---

## Lista A — Entregables a auditar

| ID | Entregable | Path |
|----|------------|------|
| A1 | CLI `quantlab-workbench` | `src/quantlab/workbench/launch.py` |
| A2 | ThreadingHTTPServer loopback | `src/quantlab/workbench/server.py` |
| A3 | JSON API + WorkbenchState | `src/quantlab/workbench/api.py` |
| A4 | SPA + CSS | `workbench/static/index.html`, `static/css/workbench.css` |
| A5 | WindowManager MDI | `workbench/static/js/wm.js` |
| A6 | Shell + panes Health/MD/Blotter | `static/js/shell.js`, `static/js/panes/` |
| A7 | Entry point pyproject | `pyproject.toml` → `quantlab-workbench` |
| A8 | LIVE gate intacto | `src/quantlab/execution/live_gate.py` (`LIVE_BLOCKED=True`) |
| A9 | Spec DoD F20 | `docs/FASE_20_WORKBENCH.md` |
| A10 | DEC-061 | `learning/decisiones.txt` |
| A11 | Suite unit workbench | `tests/unit/workbench/` (11 tests) |
| A12 | Implementation report | `docs/audit/FASE_20_IMPLEMENTATION_REPORT.md` |

---

## Lista B — Evidencia QA

```
uv run mypy --strict src/quantlab     → Success (142 files)
uv run ruff check src/quantlab        → All checks passed
uv run pytest tests/unit/workbench -q → 11 passed
uv run quantlab-health                → ok=true, live_blocked=true,
                                         operating_mode=tester, v0.12.0,
                                         venues=['a3','binance','paper']
```

Probes adicionales:

- `DEFAULT_HOST == "127.0.0.1"`
- POST `/api/mode` `live` → 400
- `quantlab-workbench --mode live` → exit 2
- Connect → `paper_broker: True` + `isinstance(broker, PaperBroker)`
- `WindowManager` en `wm.js` servido

---

## Invariantes

- LIVE order routing: **BLOQUEADO**
- Workbench bind default: **127.0.0.1**
- Órdenes workbench: **solo PaperBroker** (nunca `place_order` venue)
- Flip `LIVE_BLOCKED`: **NO ejecutado**
- Sin certificado externo hasta APROBADO Meta-Auditor externo
- Chat (F22) / paneles F21: **fuera de alcance**

---

## Pedido al Meta-Auditor externo (futuro)

1. Revisar Lista A+B + `INTERNAL_AUDIT_F20.md`.  
2. Emitir **APROBADO** / observaciones.  
3. Solo con APROBADO → generar `docs/audit/FASE_20_APPROVED.md`.
