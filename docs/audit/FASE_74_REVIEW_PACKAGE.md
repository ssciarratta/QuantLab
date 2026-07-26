# FASE 74 — Review Package INTERNAL (Status Bar Clock Timezone)

**Versión:** 0.66.0 · tip `ce0d5d1`  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** True  
**Veredicto:** **APROBADO_INTERNO**  
**Certificado externo:** `FASE_74_APPROVED.md` **NO** emitido

## Alcance

Settings `timezone` (default UTC; UTC|local) + status bar clock que respeta la preferencia vía JS.

## Evidencia

| Pieza | Path |
|-------|------|
| Spec | `docs/FASE_74_CLOCK_TZ.md` |
| Implementation report | `docs/audit/FASE_74_IMPLEMENTATION_REPORT.md` |
| AUTO AUDIT | `docs/audit/AUTO_AUDIT_2026-07-26_F74.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F74.md` |
| Noche | `docs/audit/INTERNAL_AUDIT_F19_F74_NIGHT.md` |
| Bundle | `reports/QuantLab_Internal_Review_F19_F74_v0.66.0.zip` |
| Suite | `tests/unit/workbench/test_clock_timezone_f74.py` |
| Smoke | `scripts/internal_audit_smoke.py` · check_f74 |

## Invariantes

- LIVE_BLOCKED=True  
- Sin FASE_74_APPROVED  
- DEC-118  
- `phases_summary == "F19–F74 INTERNAL"`  
- Default timezone **UTC**

## QA snapshot

pytest **1033** · smoke **59/59** · mypy strict 188 · ruff · quantlab-health 0.66.0
