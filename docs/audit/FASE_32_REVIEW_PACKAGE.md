# FASE 32 — Review Package INTERNAL (Validation / Walk-Forward Runner)

**Fecha:** 2026-07-26  
**Versión código (impl F32):** 0.24.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Tipo:** Review Package **INTERNAL** (no certificado externo)

---

## Resumen ejecutivo

F32 cablea `quantlab.validation` al workbench: runner de train/val/OOS + walk-forward sobre barras sintéticas, con índices de segmentos, resumen anti-leakage y persistencia en session `validation/`. Sin flip LIVE.

**Opción elegida:** POST `/api/lab/validation/run` persiste `summary.json` bajo `validation/<run_id>/`; GET lista/latest (+ preview efímero si vacío); panel UI tablas + historial (DEC-076).

---

## Artefactos

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Persist validation runs | `src/quantlab/workbench/validation_runs.py` |
| A2 | Session validation_dir | `workbench/session.py` |
| A3 | Lab runner | `workbench/lab_services.py` |
| A4 | API + server | `api.py` · `server.py` |
| A5 | UI Validation | `static/js/panes/validation.js` |
| A6 | Spec | `docs/FASE_32_VALIDATION_UI.md` |
| A7 | Implementation report | `docs/audit/FASE_32_IMPLEMENTATION_REPORT.md` |
| A8 | DEC-076 | `learning/decisiones.txt` |
| A9 | Suite unit F32 | `tests/unit/workbench/test_validation_f32.py` |
| A10 | Smoke F32 | `scripts/internal_audit_smoke.py` |
| A11 | Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F32.md` |
| A12 | Version 0.24.0 | `pyproject.toml` |

---

## QA ejecutado

```text
uv run quantlab-health                → ok=true, live_blocked=true, version=0.24.0
uv run python scripts/internal_audit_smoke.py  → 18/18 PASS
uv run pytest -q                      → 643 passed
```

Invariantes:
- `LIVE_BLOCKED is True`
- Persist path-safe (sesión)
- Empty-ok preview en GET

---

## Límites (INTERNAL)

- **No** emite `FASE_32_APPROVED.md`
- **No** autoriza flip LIVE
- **No** certifica UI de multiple-testing sobre p-values de estrategia

## Fuera de alcance verificado

- Flip `LIVE_BLOCKED`: **NO ejecutado**
- Auth WAN / Electron
- Bars/venue live para splits
