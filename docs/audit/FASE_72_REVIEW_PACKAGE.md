# FASE 72 — Review Package INTERNAL (Desktop Notifications)

**Versión:** 0.64.0 · tip `1b7df41`  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** True  
**Veredicto:** **APROBADO_INTERNO**  
**Certificado externo:** `FASE_72_APPROVED.md` **NO** emitido

## Alcance

Settings opt-in `desktop_notifications` + JS Notification API en toast errors / kill engage.

## Evidencia

| Pieza | Path |
|-------|------|
| Spec | `docs/FASE_72_NOTIFICATIONS.md` |
| Implementation report | `docs/audit/FASE_72_IMPLEMENTATION_REPORT.md` |
| AUTO AUDIT | `docs/audit/AUTO_AUDIT_2026-07-26_F72.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F72.md` |
| Noche | `docs/audit/INTERNAL_AUDIT_F19_F72_NIGHT.md` |
| Bundle | `reports/QuantLab_Internal_Review_F19_F72_v0.64.0.zip` |
| Suite | `tests/unit/workbench/test_desktop_notifications_f72.py` |
| Smoke | `scripts/internal_audit_smoke.py` · check_f72 |

## Invariantes

- LIVE_BLOCKED=True  
- Sin FASE_72_APPROVED  
- DEC-116  
- `phases_summary == "F19–F72 INTERNAL"`  
- Default notifications **off** (opt-in)

## QA snapshot

pytest **1017** · smoke **57/57** · mypy strict 188 · ruff · quantlab-health 0.64.0
