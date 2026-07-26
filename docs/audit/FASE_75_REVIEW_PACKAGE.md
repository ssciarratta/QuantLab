# FASE 75 — Review Package INTERNAL (Broker Heartbeat Status)

**Versión:** 0.67.0 · tip `c506ab6`  
**Branch:** `cursor/modo-real-workbench-aafd`  
**LIVE_BLOCKED:** True  
**Veredicto:** **APROBADO_INTERNO**  
**Certificado externo:** `FASE_75_APPROVED.md` **NO** emitido

## Alcance

`GET /api/broker/heartbeat` (`broker.health()` o disconnected) + status bar ok/fail + shell poll N=5s.

## Evidencia

| Pieza | Path |
|-------|------|
| Spec | `docs/FASE_75_HEARTBEAT.md` |
| Implementation report | `docs/audit/FASE_75_IMPLEMENTATION_REPORT.md` |
| AUTO AUDIT | `docs/audit/AUTO_AUDIT_2026-07-26_F75.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F75.md` |
| Noche | `docs/audit/INTERNAL_AUDIT_F19_F75_NIGHT.md` |
| Bundle | `reports/QuantLab_Internal_Review_F19_F75_v0.67.0.zip` |
| Suite | `tests/unit/workbench/test_broker_heartbeat_f75.py` |
| Smoke | `scripts/internal_audit_smoke.py` · check_f75 |

## Invariantes

- LIVE_BLOCKED=True  
- Sin FASE_75_APPROVED  
- DEC-119  
- `phases_summary == "F19–F75 INTERNAL"`  
- `HEARTBEAT_POLL_SECONDS == 5`

## QA snapshot

pytest **1041** · smoke **60/60** · mypy strict 188 · ruff · quantlab-health 0.67.0
