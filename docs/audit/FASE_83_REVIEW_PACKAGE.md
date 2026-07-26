# FASE 83 — Review Package (INTERNAL)

**Fecha:** 2026-07-26  
**Versión:** 0.75.0 · tip *(post-commit)*  
**Branch:** `cursor/modo-real-workbench-aafd`

## Resumen

Minimize all / Restore all windows vía command palette + menú Inicio; `wm.minimizeAll` / `wm.restoreAll` + `scheduleSave` persisten `minimized` en layout. DEC-127 · bump 0.75.0 · LIVE bloqueado.

## Artefactos

| Tipo | Path |
|------|------|
| Spec | `docs/FASE_83_MINIMIZE_ALL.md` |
| Implementation report | `docs/audit/FASE_83_IMPLEMENTATION_REPORT.md` |
| INTERNAL F83 | `docs/audit/INTERNAL_AUDIT_F83.md` |
| Noche F19–F83 | `docs/audit/INTERNAL_AUDIT_F19_F83_NIGHT.md` |
| AUTO audit | `docs/audit/AUTO_AUDIT_2026-07-26_F83.md` |
| Bundle | `reports/QuantLab_Internal_Review_F19_F83_v0.75.0.zip` |

## Lista A

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | minimizeAll/restoreAll | `static/js/wm.js` |
| A2 | Commands | `workbench/commands.py` |
| A3 | Spec | `docs/FASE_83_MINIMIZE_ALL.md` |
| A4 | DEC-127 | `learning/decisiones.txt` |
| A5 | Version 0.75.0 | `pyproject.toml` |
| A6 | Smoke F83 | `scripts/internal_audit_smoke.py` |
| A7 | Bundle to-phase 83 | `scripts/build_internal_review_bundle.py` |

## QA

pytest · smoke · mypy strict · ruff · quantlab-health 0.75.0

**Veredicto INTERNAL:** APROBADO_INTERNO · **sin** `FASE_83_APPROVED.md`
