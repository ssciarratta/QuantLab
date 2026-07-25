# Autauditoría exhaustiva QuantLab — 2026-07-25

**Versión:** 0.9.0  
**QA snapshot (post-hardening):** 201+ passed · mypy strict · ruff  
**Canvas:** `quantlab-self-audit.canvas.tsx`  
**Agentes/acciones:** `docs/ops/HARDENING_AGENTS.md` (A0–A7 ✅)  
**Checklist:** `docs/ops/RESEARCH_PROD_CHECKLIST.md`

---

## Veredicto

| Modo | ¿Listo? |
|------|---------|
| **Research-prod** (lab reproducible, CI doc, sin secretos, LIVE fail-closed) | **SÍ** — gaps CRITICAL/HIGH del plan A1–A7 cerrados |
| **Trading-prod** (routing real, reconciliación, HA) | **NO** — bloqueado por diseño + TD-03 |

QuantLab es un laboratorio de investigación certificado F0–F17. “Poner en producción” = **research-prod seguro**, no trading live.

---

## CRITICAL

| ID | Hallazgo | Estado |
|----|----------|--------|
| C1 | PAT `ghp_*` embebido en `git remote` | ✅ Cerrado |
| C2 | `live_gate` no cablea A3 / PyRofex | ✅ Cerrado (fail-closed universal) |
| C3 | Capa `data/exchanges/a3` puede enviar órdenes | ✅ Cerrado (`NullRouter` default) |

## HIGH

| ID | Hallazgo | Estado |
|----|----------|--------|
| H1 | `ParallelBatchRunner` traga excepciones | ✅ `strict=True` → ExceptionGroup |
| H2 | `verify_dataset` no hashea storage | ✅ SHA-256 real |
| H3 | CI Actions ausente | ✅ Fuente `docs/ci/ci.yml.example`; push workflow bloqueado por OAuth sin scope `workflow` |
| H4 | Storage sin WAL / Parquet no atómico | ✅ WAL + `.tmp`+`os.replace` |
| H5 | Accounting omite fills huérfanos | ✅ ValidationError |
| H6 | Docs `Roadmap.md` contradictorio | ✅ Índice → `ROADMAP_ALIGNED.md` |
| H7 | Observabilidad = solo structlog | ✅ Mitigado: `infra/ops_metrics.py` (contadores in-process) |

## MEDIUM / LOW (residuales)

- TD-04 LogReturn float · TD-05 latencia wall-clock · TD-03 ledger distribuido  
- TD-11/12/13/17 research/accounting menores  
- Cobertura: seguir subiendo en módulos scale/DuckDB (no bloqueante)

---

## Definición de Done — Research-prod

- [x] Token GitHub revocado + remote limpio  
- [x] Ningún `send_order` alcanzable sin `assert_live_routing_blocked`  
- [x] `execution.enabled: false` default  
- [x] CI documentado / bloqueo de push workflow documentado  
- [x] `verify_dataset` real + accounting fail-closed  
- [x] Batch strict + suite E2E research sin LIVE  
- [x] Docs únicas (`ROADMAP_ALIGNED` como verdad)  
- [x] Ops metrics mínimas + zip-slip en `restore_backup`

**LIVE order routing sigue BLOQUEADO.**
