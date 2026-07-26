# FASE 86 — Review Package (INTERNAL)

**Fecha:** 2026-07-26  
**Versión:** 0.78.0 · tip aa6266f  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** True  
**Certificado externo:** **NO** (`FASE_86_APPROVED.md` no emitido)

## Resumen

Maximize / Restore Window vía command palette + menú Inicio + titlebar button/dblclick; `wm.maximize` / `wm.restoreFromMaximize` + store `preMax` + persist/restore `maximized`. DEC-130 · bump 0.78.0 · LIVE bloqueado.

## Artefactos

| Tipo | Path |
|------|------|
| Spec | `docs/FASE_86_MAXIMIZE.md` |
| Implementation | `docs/audit/FASE_86_IMPLEMENTATION_REPORT.md` |
| INTERNAL | `docs/audit/INTERNAL_AUDIT_F86.md` |
| Noche F19–F86 | `docs/audit/INTERNAL_AUDIT_F19_F86_NIGHT.md` |
| Auto-audit | `docs/audit/AUTO_AUDIT_2026-07-26_F86.md` |
| Bundle | `reports/QuantLab_Internal_Review_F19_F86_v0.78.0.zip` |

## Lista A (checklist rápido)

| ID | Check | Evidencia |
|----|-------|-----------|
| A1 | maximize/restore + preMax | `wm.js` |
| A2 | Commands | `commands.py` |
| A3 | Palette + menú + titlebar | `command_palette.js` · `index.html` |
| A4 | Spec + DEC-130 | `FASE_86_MAXIMIZE.md` · `decisiones.txt` |
| A5 | Version 0.78.0 | `pyproject.toml` |
| A6 | Sin FASE_86_APPROVED | filesystem |
| A7 | LIVE_BLOCKED | `live_gate.py` |

## QA

pytest · smoke · mypy strict · ruff · quantlab-health 0.78.0
