# FASE 84 — Review Package (INTERNAL)

**Fecha:** 2026-07-26  
**Versión:** 0.76.0 · tip e82ebef  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Veredicto INTERNAL:** **APROBADO_INTERNO** · sin certificado externo

## Resumen

Cascade / Tile windows vía command palette + menú Inicio; `wm.cascadeWindows` / `wm.tileWindows` + pure rects + `scheduleSave` persisten layout. DEC-128 · bump 0.76.0 · LIVE bloqueado.

## Artefactos

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_84_CASCADE_TILE.md` |
| Implementation report | `docs/audit/FASE_84_IMPLEMENTATION_REPORT.md` |
| INTERNAL F84 | `docs/audit/INTERNAL_AUDIT_F84.md` |
| Noche F19–F84 | `docs/audit/INTERNAL_AUDIT_F19_F84_NIGHT.md` |
| AUTO audit | `docs/audit/AUTO_AUDIT_2026-07-26_F84.md` |
| Bundle | `reports/QuantLab_Internal_Review_F19_F84_v0.76.0.zip` |

## Lista A

| ID | Check | Path |
|----|-------|------|
| A1 | cascade/tile + rects | `static/js/wm.js` |
| A2 | Python mirror | `workbench/window_layout.py` |
| A3 | Commands | `workbench/commands.py` |
| A4 | DEC-128 | `learning/decisiones.txt` |
| A5 | Version 0.76.0 | `pyproject.toml` |
| A6 | Smoke F84 | `scripts/internal_audit_smoke.py` |
| A7 | Bundle to-phase 84 | `scripts/build_internal_review_bundle.py` |

## QA

pytest · smoke · mypy strict · ruff · quantlab-health 0.76.0

**NO** incluye `FASE_84_APPROVED.md`.
