# Autauditoría exhaustiva QuantLab — 2026-07-25

**Versión:** 0.10.0  
**QA:** mypy strict · ruff · pytest · `quantlab-health`  
**Canvas:** `quantlab-self-audit.canvas.tsx`  
**Agentes:** `docs/ops/HARDENING_AGENTS.md` (A0–A7 ✅)  
**Checklist:** `docs/ops/RESEARCH_PROD_CHECKLIST.md`  
**Tests cierre:** `test_self_audit_closure.py` · `test_noncritical_residuals.py`

---

## Veredicto

| Modo | ¿Listo? |
|------|---------|
| **Research-prod** | **SÍ** — críticos + high + medium + residuales no críticos accionables cerrados |
| **Trading-prod** | **NO** — LIVE + TD-03 HA fuera de alcance |

---

## CRITICAL / HIGH / MEDIUM

Todos ✅ (C1–C3, H1–H5, M1–M2). Detalle en historial de hardening A0–A7.

## Residuales no críticos (cerrados esta ola)

| ID | Hallazgo | Fix |
|----|----------|-----|
| R9 | `freeze_mapping` solo superficial | Deep-freeze nested dict/list/set |
| R3 | ATR vs Wilder confuso | Doc + `metadata.method=sma_tr` |
| R5 | Calmar calendario implícito | Doc bar-based + test |
| TD-12 | `mark_equity` 2× | Diseño documentado + test regresión |
| TD-06 | Explain parcial | `*_n` + contrib/share; suma = composite |
| TD-09 | FeatureStore remoto | Aceptado local; rechazo URL |
| OPS-PROM | Sin export scrapable | `render_prometheus_text` + health export |

## Fuera de alcance (explícito)

- LIVE / TD-10 order routing real  
- `FASE_18_APPROVED` (solo Meta-Auditor)  
- TD-03 HA/ACID multi-nodo (trading-prod)

**LIVE order routing sigue BLOQUEADO.**
