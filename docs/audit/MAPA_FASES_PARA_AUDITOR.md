# Mapa oficial de fases QuantLab — para Meta-Auditor

**Fuente de verdad:** `docs/ROADMAP_ALIGNED.md`  
**Fecha:** 2026-07-26  
**Código actual:** 0.16.0 (F24) · F23 audit INTERNAL 0.15.0  
**LIVE order routing:** BLOQUEADO (`LIVE_BLOCKED = True`)  
**Arco F19–F22:** `docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md` (**APROBADO_INTERNO**)  
**F23:** `docs/audit/INTERNAL_AUDIT_F23.md` (**APROBADO_INTERNO**)  
**F24:** `docs/audit/INTERNAL_AUDIT_F24.md` (**APROBADO_INTERNO**)

> Nota: en `Arquitectura.md` §13 el roadmap original terminaba en **Fase 17**.  
> **F18** = research-ops; **F19** = Operating Modes + BrokerPort; **F20** = Workbench;  
> **F21** = Lab Panels; **F22** = Chat IA; **F23** = Paper Book + sesión + risk;  
> **F24** = venue plugins + MD read-only.  
> **No confundir “no estaba en Arquitectura §13” con “no existe en el repo”.**

---

## Tabla F0–F24 (verificar certificados)

| Fase | Nombre | Certificado formal | Path certificado / evidencia | Estado auditoría |
|------|--------|--------------------|------------------------------|------------------|
| 0 | Fundación del repositorio | ✅ | (fundación) | Cerrada |
| 1 | Diseño de arquitectura | ✅ | Arquitectura v1.1 + DECs | Cerrada |
| 2 | Dominio, manifests y CI | ✅ | `docs/audit/FASE_02_APPROVED.md` | **APROBADA** |
| 3 | Datos, catálogo y calidad | ✅ | `docs/audit/FASE_03_APPROVED.md` | **APROBADA** |
| 4 | Vertical slice + sim/metrics/scanner MVP | ✅ | `docs/audit/FASE_04_APPROVED.md` | **APROBADA** |
| 5 | Features (oficial) | ✅ | `docs/audit/FASE_05_OFFICIAL_APPROVED.md` | **APROBADA** |
| 6 | Backtester bar-based (5A) | ✅ | `docs/audit/FASE_06_APPROVED.md` | **APROBADA** |
| 7 | Backtester microestructura (5B) | ✅ | `docs/audit/FASE_07_APPROVED.md` | **APROBADA** |
| 8 | Métricas y reporting | ✅ | `docs/audit/FASE_08_APPROVED.md` | **APROBADA** |
| 9 | Experiment Registry + artifacts | ✅ | `docs/audit/FASE_09_APPROVED.md` | **APROBADA** |
| 10 | Scientific Validation | ✅ | `docs/audit/FASE_10_TO_16_APPROVED.md` + residuos F17 | **APROBADA** |
| 11 | Monte Carlo | ✅ | `docs/audit/FASE_10_TO_16_APPROVED.md` | **APROBADA** |
| 12 | Optimizer (+ Pareto residual) | ✅ | `FASE_10_TO_16` + residual en F17 | **APROBADA** |
| 13 | Alpha Scanner | ✅ | `docs/audit/FASE_10_TO_16_APPROVED.md` | **APROBADA** |
| 14 | Estrategias avanzadas (+ Avellaneda residual) | ✅ | `FASE_10_TO_16` + residual en F17 | **APROBADA** |
| 15 | Multi-exchange | ✅ | `docs/audit/FASE_10_TO_16_APPROVED.md` | **APROBADA** |
| 16 | Hummingbot export v1 | ✅ | `docs/audit/FASE_10_TO_16_APPROVED.md` | **APROBADA** |
| 17 | Escalabilidad + residuos F10/F12/F14 | ✅ | `docs/audit/FASE_17_APPROVED.md` | **APROBADO DEFINITIVO** (2026-07-25) |
| **18** | **Control Total (research-ops)** | ✅ | `docs/audit/FASE_18_APPROVED.md` | **APROBADO DEFINITIVO** (2026-07-25) |
| **19** | **Operating Modes + BrokerPort** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F19.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **20** | **Workbench (1-click / WM)** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F20.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **21** | **Lab Panels** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F21.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **22** | **Chat IA safe-by-default** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F22.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **23** | **Paper Book + Session + Risk** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F23.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **24** | **Venue plugins + MD read-only** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F24.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |

---

## Fase 18 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / alcance | `docs/FASE_18_CONTROL.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 18** |
| Review Package (trabajo) | `docs/audit/FASE_18_REVIEW_PACKAGE.md` |
| Implementation report | `docs/audit/FASE_18_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-25_F18.md` |
| Checklist research-prod | `docs/ops/RESEARCH_PROD_CHECKLIST.md` |

**Certificado emitido:** `docs/audit/FASE_18_APPROVED.md` (APROBADO DEFINITIVO Meta-Auditor, 2026-07-25).

### Lista A F18 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | FeatureStore anti-colisión (TD-13) | `src/quantlab/features/store.py` |
| A2 | LogReturn `Decimal.ln` (TD-04) | `src/quantlab/features/transformers.py` |
| A3 | Convención TD-17 `gross_excluding_fees` | `src/quantlab/backtester/accounting.py` |
| A4 | LocalPaperLedger + federación research | `src/quantlab/ledger/` |
| A5 | Health / ops (`quantlab-health`) | `src/quantlab/infra/health.py` |
| A6 | TD-05 `min_delay` wall-clock | `src/quantlab/execution/latency.py` |
| A7 | CI Actions | `.github/workflows/ci.yml` |
| A8 | Suite F18 | `tests/unit/fase18/` |
| A9 | LIVE gate intacto | `execution/live_gate.py` |

### Lista B F18 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest -q
uv run quantlab-health
```

Versión código F18: **0.10.0** · LIVE: **BLOQUEADO**.

---

## Fase 19 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / alcance | `docs/FASE_19_OPERATING_MODES.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 19** |
| Review Package INTERNAL | `docs/audit/FASE_19_REVIEW_PACKAGE.md` |
| Implementation report | `docs/audit/FASE_19_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F19.md` |
| Veredicto INTERNAL | `docs/audit/INTERNAL_AUDIT_F19.md` |
| LIVE flip checklist | `docs/ops/LIVE_FLIP_CHECKLIST.md` |
| Spec F20 (implementada) | `docs/FASE_20_WORKBENCH.md` |

**Certificado externo:** **NO** emitido (`FASE_19_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F19 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | OperatingMode + ModeGuard + REAL=PAPER | `src/quantlab/brokers/mode.py` |
| A2 | BrokerPort + DTOs | `brokers/port.py`, `brokers/types.py` |
| A3 | BrokerRegistry (a3/binance/paper) | `brokers/registry.py` |
| A4 | PaperBroker + PaperFillJournal | `brokers/paper/` |
| A5 | A3BrokerPort MD-only | `brokers/a3/adapter_port.py` |
| A6 | FakeBinanceBroker | `brokers/binance/fake.py` |
| A7 | LIVE gate intacto | `execution/live_gate.py` |
| A8 | Health operating_mode | `infra/health.py` |
| A9 | Suite brokers | `tests/unit/brokers/` |

### Lista B F19 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest tests/unit/brokers -q
uv run quantlab-health
```

Versión código F19: **0.11.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 20 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / alcance | `docs/FASE_20_WORKBENCH.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 20** |
| Review Package INTERNAL | `docs/audit/FASE_20_REVIEW_PACKAGE.md` |
| Implementation report | `docs/audit/FASE_20_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F20.md` |
| Veredicto INTERNAL | `docs/audit/INTERNAL_AUDIT_F20.md` |

**Certificado externo:** **NO** emitido (`FASE_20_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F20 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | CLI `quantlab-workbench` | `workbench/launch.py` |
| A2 | ThreadingHTTPServer loopback | `workbench/server.py` |
| A3 | JSON API + WorkbenchState | `workbench/api.py` |
| A4 | SPA + WindowManager | `workbench/static/` (`wm.js`) |
| A5 | Paneles Health / MD / Blotter | `static/js/panes/` |
| A6 | LIVE gate intacto | `execution/live_gate.py` |
| A7 | DEC-061 | `learning/decisiones.txt` |
| A8 | Suite workbench | `tests/unit/workbench/` |

### Lista B F20 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest tests/unit/workbench -q
uv run quantlab-health
```

Versión código F20: **0.12.0** · LIVE: **BLOQUEADO** · bind default: **127.0.0.1** · flip: **NO**.

---

## Fase 21 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / alcance | `docs/FASE_21_LAB_PANELS.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 21** |
| Review Package INTERNAL | `docs/audit/FASE_21_REVIEW_PACKAGE.md` |
| Implementation report | `docs/audit/FASE_21_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F21.md` |
| Veredicto INTERNAL | `docs/audit/INTERNAL_AUDIT_F21.md` |

**Certificado externo:** **NO** emitido (`FASE_21_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F21 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Lab adapters | `workbench/lab_services.py` |
| A2 | Handlers `/api/lab/*` | `workbench/api.py` |
| A3 | Rutas HTTP lab | `workbench/server.py` |
| A4 | Paneles lab + shell | `static/js/panes/*`, `shell.js` |
| A5 | LIVE gate intacto | `execution/live_gate.py` |
| A6 | DEC-062 | `learning/decisiones.txt` |
| A7 | Suite lab API | `tests/unit/workbench/test_lab_api.py` |

### Lista B F21 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest tests/unit/workbench -q
uv run quantlab-health
```

Versión código F21: **0.13.0** · LIVE: **BLOQUEADO** · bind default: **127.0.0.1** · flip: **NO**.

---

## Fase 22 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / alcance | `docs/FASE_22_CHAT_IA.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 22** |
| Review Package INTERNAL | `docs/audit/FASE_22_REVIEW_PACKAGE.md` |
| Implementation report | `docs/audit/FASE_22_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F22.md` |
| Veredicto INTERNAL | `docs/audit/INTERNAL_AUDIT_F22.md` |
| Cierre arco F19–F22 | `docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md` |

**Certificado externo:** **NO** emitido (`FASE_22_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F22 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | ToolRegistry allowlist | `workbench/chat/tools.py` |
| A2 | Providers (Fake default) | `workbench/chat/providers.py` |
| A3 | Audit JSONL | `workbench/chat/audit.py` |
| A4 | Orchestrator + API | `orchestrator.py`, `api.py`, `server.py` |
| A5 | Panel Chat + banner | `static/js/panes/chat.js` |
| A6 | LIVE gate intacto | `execution/live_gate.py` |
| A7 | DEC-063..065 | `learning/decisiones.txt` |
| A8 | Suite chat | `tests/unit/workbench/test_chat_*.py` |

### Lista B F22 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F22: **0.14.0** · LIVE: **BLOQUEADO** · FakeProvider default · flip: **NO**.

---

## Fase 23 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / alcance | `docs/FASE_23_PAPER_BOOK.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 23** |
| Review Package INTERNAL | `docs/audit/FASE_23_REVIEW_PACKAGE.md` |
| Implementation report | `docs/audit/FASE_23_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F23.md` |
| Veredicto INTERNAL | `docs/audit/INTERNAL_AUDIT_F23.md` |

**Certificado externo:** **NO** emitido (`FASE_23_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F23 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | `PaperBook` | `brokers/paper/book.py` |
| A2 | `PaperBroker` + book | `brokers/paper/broker.py` |
| A3 | `WorkbenchSession` | `workbench/session.py` |
| A4 | `PaperRiskLimits` | `workbench/risk.py` |
| A5 | API positions/book/session | `workbench/api.py` + `server.py` |
| A6 | Panel Posiciones | `static/js/panes/positions.js` |
| A7 | LIVE gate intacto | `execution/live_gate.py` |
| A8 | DEC-066 | `learning/decisiones.txt` |
| A9 | Suite paper/session/risk/API | `tests/unit/brokers/test_paper_book.py`, `tests/unit/workbench/test_*` |

### Lista B F23 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión impl F23: **0.15.0** (`9b89274`) · LIVE: **BLOQUEADO** · remediación H1/H2 · flip: **NO**.

---

## Fase 24 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / DoD | `docs/FASE_24_VENUE_MD_PLUGINS.md` |
| Ops plugins | `docs/ops/BROKER_PLUGINS.md` |
| Implementation report | `docs/audit/FASE_24_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F24.md` |
| Review Package INTERNAL | `docs/audit/FASE_24_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F24.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 24** |

**Estado:** **APROBADO_INTERNO** v0.16.0 (`c846e81` + remediación H1 `25f7ba1`).  
**LIVE:** BLOQUEADO · DEC-067/068 · `FASE_24_APPROVED.md` **NO** emitido.

---

## Mensaje corto para el auditor

1. F0–F18 certificado formal externo; F19–F24 **APROBADO_INTERNO**.  
2. QuantLab v0.16.0: venue plugins + A3 MD env opt-in + generics sobre F23 PaperBook.  
3. **LIVE sigue BLOQUEADO**; REAL = PAPER ≠ LIVE; MD env no habilita submit venue.  
4. Arco F19–F22 + F23 + F24 INTERNAL; remediación F24 H1 (no plugin shadow).  
5. **No** emitir `FASE_*_APPROVED.md` desde INTERNAL.
