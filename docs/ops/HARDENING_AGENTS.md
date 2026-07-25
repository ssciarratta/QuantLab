# Plan de acciones y agentes — Research-Prod QuantLab

**Fecha:** 2026-07-25  
**Objetivo:** cerrar CRITICAL/HIGH de `docs/audit/SELF_AUDIT_2026-07-25.md`  
**Fuera de alcance:** order routing LIVE real (sigue BLOQUEADO)

---

## Estado global

| Agente | Estado |
|--------|--------|
| A0 Security | ✅ |
| A1 Live-Gate | ✅ |
| A2 NullRouter | ✅ |
| A3 Scale | ✅ |
| A4 Integrity | ✅ |
| A5 Metrics | ✅ |
| A6 CI / Docs | ✅ |
| A7 Research-Prod Gate | ✅ |

Checklist: `docs/ops/RESEARCH_PROD_CHECKLIST.md` — todo ✅. LIVE sigue BLOQUEADO.

---

## Cómo usar

1. Abrí un **chat nuevo** por agente (una cosa por vez).  
2. Pegá el bloque **Prompt** del agente.  
3. Exigí DoD al final: tests + mypy strict + ruff.  
4. No emitir certificados falsos; no habilitar LIVE.

Orden obligatorio: **A0 → A1 → A2 → … → A7**.

---

## A0 — Security (cerrado 2026-07-25)

**Estado:** ✅
- Remote sin token embebido
- PAT classic `ghp_*` revocado vía `POST /credentials/revoke` (verify HTTP 401)
- Credential Manager limpiado; `gh auth setup-git` (`gho_*` keyring)

---

## A1 — Live-Gate Hardening ✅

**DoD:** todo path a `send_order`/`cancel_order` falla si `LIVE_BLOCKED`; tests red-team.

Implementado: `_enforce_live_blocked` en A3Adapter; `assert_live_routing_blocked` en PyRofexBackend; `execution.enabled: false`.

---

## A2 — Architecture Split (NullRouter) ✅

**DoD:** data A3 no importa backend de órdenes reales por default.

Implementado: `OrderRouter` / `NullRouter` / `GatedBackendRouter` en `execution/order_router.py` (sin import circular runtime hacia `a3`).

---

## A3 — Scale Hardening ✅

**DoD:** batch strict; monitor con Lock; Parquet temp+rename.

Implementado: `ParallelBatchRunner(strict=True)` → `ExceptionGroup`; `ProgressMonitor` + Lock; Parquet `.tmp`+`os.replace`; SQLite WAL.

---

## A4 — Integrity ✅

**DoD:** verify_dataset hashea archivo; accounting reporta fills huérfanos.

Implementado: SHA-256 real en SQLite/DuckDB; checksum A3 = hash del JSONL; orphan fills → `ValidationError`.

---

## A5 — Metrics Cleanup ✅

**DoD:** sin sentinel 999; convención Sharpe/Sortino documentada + tests.

Implementado: `profit_factor` → `None` / `"undefined"`; Sortino con divisor muestral `(N-1)`.

---

## A6 — CI / Docs Ops ✅

**DoD:** workflow en repo; Roadmap alineado.

Implementado: fuente CI en `docs/ci/ci.yml.example`; push de `.github/workflows/` requiere scope OAuth `workflow` (bloqueado 2026-07-25). `docs/Roadmap.md` → `ROADMAP_ALIGNED.md`.

---

## A7 — Research-Prod Gate (cierre) ✅

**DoD:** checklist todo verde.

Ver `docs/ops/RESEARCH_PROD_CHECKLIST.md`. Sin nuevo `FASE_*_APPROVED`. LIVE BLOQUEADO.

---

## Agentes Cursor sugeridos (roles)

| Agente | Skill Cursor | Foco |
|--------|--------------|------|
| Security | `review-security` | C1, secret scan |
| Live-Gate | generalPurpose | C2–C3 |
| Architecture | `architecture-reviewer` → implement | A2 |
| Scale | `performance-optimization` | A3 |
| Integrity | `data-engineering` | A4 |
| Metrics | `quant-analyst` | A5 |
| CI | shell / generalPurpose | A6 |
| Gate final | `continuous-improvement` | A7 |
