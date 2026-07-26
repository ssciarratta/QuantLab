# Review Package — FASE 28 Layout Persistence + Journal Viewer

**Fecha:** 2026-07-26  
**Versión código (impl F28):** 0.20.0  
**Tipo:** Review Package **INTERNAL** (Meta-Auditor INTERNO Zero-Trust)  
**Implementación:** commit `86517cf`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F28.md`  
**Veredicto INTERNAL:** `docs/audit/INTERNAL_AUDIT_F28.md`  
**Implementation report:** `docs/audit/FASE_28_IMPLEMENTATION_REPORT.md`

> **Aclaración:** este paquete **NO** constituye `FASE_28_APPROVED` formal del Meta-Auditor **externo**.  
> Es evidencia + Lista A/B para auditoría interna y para un futuro Review Package externo.

---

## Architecture Review (resumen)

**Opción elegida:** `layout.json` por sesión durable + API GET/PUT; WM debounce save; panel Journal sobre fills paper existentes + CSV client-side (DEC-072).  
**Alternativa descartada:** flip LIVE / auth WAN / export CSV server-side / Electron.  
**Criterio:** research-safe — solo persistencia UI + lectura journal paper; LIVE_BLOCKED.

---

## Lista A — Entregables a auditar

| ID | Entregable | Path |
|----|------------|------|
| A1 | Layout save/load | `src/quantlab/workbench/layout.py` |
| A2 | Session `layout_path` | `src/quantlab/workbench/session.py` |
| A3 | `GET`/`PUT` `/api/layout` | `workbench/api.py` + `server.py` |
| A4 | WM debounce + restore | `static/js/wm.js`, `shell.js`, `api.js` |
| A5 | Panel Journal + CSV | `static/js/panes/journal.js` + `index.html` |
| A6 | LIVE gate intacto | `execution/live_gate.py` |
| A7 | Spec DoD F28 | `docs/FASE_28_LAYOUT_JOURNAL.md` |
| A8 | DEC-072 | `learning/decisiones.txt` |
| A9 | Suite unit F28 | `tests/unit/workbench/test_layout_f28.py` |
| A10 | Smoke F28 | `scripts/internal_audit_smoke.py` |
| A11 | Implementation report | `docs/audit/FASE_28_IMPLEMENTATION_REPORT.md` |
| A12 | Version 0.20.0 | `pyproject.toml` @ `86517cf` |

---

## Lista B — Evidencia QA

```
uv run mypy --strict src/quantlab     → Success (159 files)
uv run ruff check src/quantlab tests scripts → All checks passed
uv run pytest -q                      → 600 passed
uv run quantlab-health                → ok=true, live_blocked=true, version=0.20.0
uv run python scripts/internal_audit_smoke.py → PASS (14 checks)
```

Probes adicionales:

- `LIVE_BLOCKED is True`
- `layout.json` roundtrip atómico
- PUT inválido (version/id/rango) → 400
- Journal lee `/api/paper/fills`; CSV Blob local

---

## Remediación / hardening INTERNAL

| ID | Severidad | Fix |
|----|-----------|-----|
| — | CRITICAL | **Ninguno** |
| — | HIGH | **Ninguno** |
| Tooling | — | Bundle default to-phase **28** |

---

## Invariantes

- LIVE order routing: **BLOQUEADO**
- Layout fail-closed (ids / rangos / version)
- Journal: solo lectura fills paper
- Flip `LIVE_BLOCKED`: **NO ejecutado**
- Sin certificado externo hasta APROBADO Meta-Auditor externo

---

## Pedido al Meta-Auditor externo (futuro)

1. Revisar Lista A+B + `INTERNAL_AUDIT_F28.md` + noche F19–F28.  
2. Emitir **APROBADO** / observaciones.  
3. Solo con APROBADO → generar `docs/audit/FASE_28_APPROVED.md`.
