# Autauditoría exhaustiva QuantLab — 2026-07-25

**Versión:** 0.10.0  
**QA:** mypy strict · ruff · pytest (suite completa) · `quantlab-health`  
**Canvas:** `quantlab-self-audit.canvas.tsx` (sincronizado ✅)  
**Agentes:** `docs/ops/HARDENING_AGENTS.md` (A0–A7 ✅)  
**Checklist:** `docs/ops/RESEARCH_PROD_CHECKLIST.md`  
**Cierre residual:** `tests/unit/ops/test_self_audit_closure.py`

---

## Veredicto

| Modo | ¿Listo? |
|------|---------|
| **Research-prod** (lab reproducible, CI, sin secretos, LIVE fail-closed) | **SÍ** — C1–C3 + H1–H5 + M1–M2 cerrados |
| **Trading-prod** (routing real, reconciliación, HA) | **NO** — bloqueado por diseño + TD-03 residual |

QuantLab es laboratorio de investigación certificado F0–F17. “Producción” = **research-prod seguro**, no trading live.

---

## CRITICAL

| ID | Hallazgo | Estado |
|----|----------|--------|
| C1 | PAT `ghp_*` embebido en `git remote` | ✅ Cerrado (`check_git_remote_clean`) |
| C2 | `live_gate` no cablea A3 / PyRofex | ✅ Cerrado (fail-closed universal + red-team) |
| C3 | Capa `data/exchanges/a3` puede enviar órdenes | ✅ Cerrado (`NullRouter` default) |

## HIGH

| ID | Hallazgo | Estado |
|----|----------|--------|
| H1 | `ParallelBatchRunner` traga excepciones | ✅ `strict=True` → ExceptionGroup |
| H2 | `verify_dataset` no hashea storage | ✅ SHA-256 real |
| H3 | CI GitHub Actions ausente | ✅ `.github/workflows/ci.yml` activo |
| H4 | Storage sin WAL / Parquet no atómico | ✅ WAL + `.tmp`+`os.replace` |
| H5 | Accounting omite fills huérfanos | ✅ ValidationError |

## MEDIUM

| ID | Hallazgo | Estado |
|----|----------|--------|
| M1 | `profit_factor=999` sentinel | ✅ `None` / `"undefined"` |
| M2 | Docs `Roadmap.md` contradictorio | ✅ → `ROADMAP_ALIGNED.md` |

## Residuales no bloqueantes

- TD-03 HA/ACID multi-nodo (trading-prod)
- Cobertura DuckDB/batch/AS reforzada en `test_self_audit_closure.py`
- `FASE_18_APPROVED.md` solo con APROBADO Meta-Auditor

---

## Definición de Done — Research-prod

- [x] Token GitHub revocado + remote limpio  
- [x] Ningún `send_order` alcanzable sin live_gate  
- [x] `execution.enabled: false` default  
- [x] CI Actions activo  
- [x] `verify_dataset` real + accounting fail-closed  
- [x] Batch strict + suite sin LIVE  
- [x] Docs únicas (`ROADMAP_ALIGNED`)  
- [x] Ops metrics + zip-slip en `restore_backup`  
- [x] Canvas self-audit sincronizado con estado real  

**LIVE order routing sigue BLOQUEADO.**
