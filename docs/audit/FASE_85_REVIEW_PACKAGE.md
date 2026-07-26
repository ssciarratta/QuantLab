# FASE 85 — Review Package (INTERNAL)

**Fecha:** 2026-07-26  
**Versión:** 0.77.0 · tip PENDING  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Veredicto INTERNAL:** APROBADO_INTERNO · **sin** `FASE_85_APPROVED.md`

## Resumen

Bring to Front / Send to Back vía command palette + menú Inicio + context titlebar; `wm.bringToFront` / `wm.sendToBack` + persist/restore `z`. DEC-129 · bump 0.77.0 · LIVE bloqueado.

## Artefactos

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_85_ZORDER.md` |
| Implementation report | `docs/audit/FASE_85_IMPLEMENTATION_REPORT.md` |
| INTERNAL F85 | `docs/audit/INTERNAL_AUDIT_F85.md` |
| Noche F19–F85 | `docs/audit/INTERNAL_AUDIT_F19_F85_NIGHT.md` |
| AUTO audit | `docs/audit/AUTO_AUDIT_2026-07-26_F85.md` |
| Bundle | `reports/QuantLab_Internal_Review_F19_F85_v0.77.0.zip` |

## Lista A (rápida)

| ID | Check | Path |
|----|-------|------|
| A1 | bring/send + ctx | `static/js/wm.js` |
| A2 | Commands | `workbench/commands.py` |
| A3 | Palette / menú | `command_palette.js` · `index.html` |
| A4 | Spec + DEC-129 | `FASE_85_ZORDER.md` · `decisiones.txt` |
| A5 | Version 0.77.0 | `pyproject.toml` |
| A6 | Suite + smoke | `test_zorder_f85.py` · smoke |
| A7 | Bundle to-phase 85 | `build_internal_review_bundle.py` |

## QA

pytest · smoke · mypy strict · ruff · quantlab-health 0.77.0
