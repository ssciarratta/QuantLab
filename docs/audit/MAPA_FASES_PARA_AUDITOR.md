# Mapa oficial de fases QuantLab — para Meta-Auditor

**Fuente de verdad:** `docs/ROADMAP_ALIGNED.md`  
**Fecha:** 2026-07-26  
**Código actual:** 0.26.0 (F34) · F33 INTERNAL 0.25.0 · F32 INTERNAL 0.24.0 · F31 INTERNAL 0.23.0  
**LIVE order routing:** BLOQUEADO (`LIVE_BLOCKED = True`)  
**Arco F19–F22:** `docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md` (**APROBADO_INTERNO**)  
**Arco F23–F25:** `docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md` (**APROBADO_INTERNO**)  
**Noche F19–F25:** `docs/audit/INTERNAL_AUDIT_F19_F25_NIGHT.md` (**APROBADO_INTERNO**)  
**Noche F19–F26:** `docs/audit/INTERNAL_AUDIT_F19_F26_NIGHT.md` (**APROBADO_INTERNO**)  
**Noche F19–F27:** `docs/audit/INTERNAL_AUDIT_F19_F27_NIGHT.md` (**APROBADO_INTERNO**)  
**Noche F19–F28:** `docs/audit/INTERNAL_AUDIT_F19_F28_NIGHT.md` (**APROBADO_INTERNO**)  
**Noche F19–F29:** `docs/audit/INTERNAL_AUDIT_F19_F29_NIGHT.md` (**APROBADO_INTERNO**)  
**Noche F19–F30:** `docs/audit/INTERNAL_AUDIT_F19_F30_NIGHT.md` (**APROBADO_INTERNO**)  
**Noche F19–F31:** `docs/audit/INTERNAL_AUDIT_F19_F31_NIGHT.md` (**APROBADO_INTERNO**)  
**Noche F19–F32:** `docs/audit/INTERNAL_AUDIT_F19_F32_NIGHT.md` (**APROBADO_INTERNO**)  
**Noche F19–F33:** `docs/audit/INTERNAL_AUDIT_F19_F33_NIGHT.md` (**APROBADO_INTERNO**)  
**F23:** `docs/audit/INTERNAL_AUDIT_F23.md` (**APROBADO_INTERNO**)  
**F24:** `docs/audit/INTERNAL_AUDIT_F24.md` (**APROBADO_INTERNO**)  
**F25:** `docs/audit/INTERNAL_AUDIT_F25.md` (**APROBADO_INTERNO**)  
**F26:** `docs/audit/INTERNAL_AUDIT_F26.md` (**APROBADO_INTERNO**)  
**F27:** `docs/audit/INTERNAL_AUDIT_F27.md` (**APROBADO_INTERNO**)  
**F28:** `docs/audit/INTERNAL_AUDIT_F28.md` (**APROBADO_INTERNO**)  
**F29:** `docs/audit/INTERNAL_AUDIT_F29.md` (**APROBADO_INTERNO**)  
**F30:** `docs/audit/INTERNAL_AUDIT_F30.md` (**APROBADO_INTERNO**)  
**F31:** `docs/audit/INTERNAL_AUDIT_F31.md` (**APROBADO_INTERNO**)  
**F32:** `docs/audit/INTERNAL_AUDIT_F32.md` (**APROBADO_INTERNO**)  
**F33:** `docs/audit/INTERNAL_AUDIT_F33.md` (**APROBADO_INTERNO**)

> Nota: en `Arquitectura.md` §13 el roadmap original terminaba en **Fase 17**.  
> **F18** = research-ops; **F19** = Operating Modes + BrokerPort; **F20** = Workbench;  
> **F21** = Lab Panels; **F22** = Chat IA; **F23** = Paper Book + sesión + risk;  
> **F24** = venue plugins + MD read-only; **F25** = Ops Desk 1-click + hardening;  
> **F26** = Paper Session Runner; **F27** = Strategy Catalog;  
> **F28** = Layout persistence + Journal viewer;  
> **F29** = Report Viewer + Metrics History;  
> **F30** = Universe Watchlist + Data Catalog Browser;  
> **F31** = Feature Store Browser + Pipeline Runner UI;  
> **F32** = Validation / Walk-Forward Runner UI;  
> **F33** = Optimizer History + Pareto Panel.  
> **No confundir “no estaba en Arquitectura §13” con “no existe en el repo”.**

---

## Tabla F0–F31 (verificar certificados)

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
| **25** | **Ops Desk 1-click + hardening** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F25.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **26** | **Paper Session Runner** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F26.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **27** | **Strategy Catalog** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F27.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **28** | **Layout + Journal** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F28.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **29** | **Report Viewer + Metrics History** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F29.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **30** | **Universe Watchlist + Data Catalog** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F30.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |
| **31** | **Feature Store Browser + Pipeline Runner** | 📦 INTERNAL | `docs/audit/INTERNAL_AUDIT_F31.md` | **APROBADO_INTERNO** (2026-07-26) — externo pendiente |

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

**Estado:** **APROBADO_INTERNO** v0.16.0 (`c846e81` + remediación H1 `f8267e3`).  
**LIVE:** BLOQUEADO · DEC-067/068 · `FASE_24_APPROVED.md` **NO** emitido.

---

## Fase 25 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / DoD | `docs/FASE_25_OPS_DESK.md` |
| Ops 1-click | `docs/ops/WORKBENCH_1CLICK.md` |
| Implementation report | `docs/audit/FASE_25_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F25.md` |
| Review Package INTERNAL | `docs/audit/FASE_25_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F25.md` |
| Arco F23–F25 | `docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md` |
| Noche F19–F25 | `docs/audit/INTERNAL_AUDIT_F19_F25_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 25** |

**Certificado externo:** **NO** emitido (`FASE_25_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F25 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Launcher 1-click | `scripts/launch_workbench.sh` |
| A2 | Desktop entry | `packaging/quantlab-workbench.desktop` |
| A3 | Non-loopback gate + slip CLI | `workbench/launch.py` |
| A4 | `validate_experiment_id` | `workbench/lab_services.py` |
| A5 | Paper slippage adverso | `brokers/paper/broker.py` |
| A6 | `GET /api/risk` + Risk UI | `workbench/api.py` + `static/js/panes/risk.js` |
| A7 | LIVE gate intacto | `execution/live_gate.py` |
| A8 | DEC-069 | `learning/decisiones.txt` |
| A9 | Suite F25 | `tests/unit/workbench/test_launch_non_loopback.py`, `test_experiment_id_charset.py`, `test_api_risk.py`, `tests/unit/brokers/test_paper_slippage_bps.py` |

### Lista B F25 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F25: **0.17.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 26 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / DoD | `docs/FASE_26_PAPER_SESSION.md` |
| Implementation report | `docs/audit/FASE_26_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F26.md` |
| Review Package INTERNAL | `docs/audit/FASE_26_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F26.md` |
| Noche F19–F26 | `docs/audit/INTERNAL_AUDIT_F19_F26_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 26** |

**Certificado externo:** **NO** emitido (`FASE_26_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F26 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | `PaperSessionRunner` | `workbench/paper_session.py` |
| A2 | API `/api/paper/session/*` | `workbench/api.py` + `server.py` |
| A3 | Panel Sesión Paper | `static/js/panes/paper_session.js` |
| A4 | LIVE gate + PaperBroker-only | `execution/live_gate.py` · runner isinstance |
| A5 | DEC-070 | `learning/decisiones.txt` |
| A6 | Suite F26 | `tests/unit/workbench/test_paper_session_runner.py` |
| A7 | Smoke F26 | `scripts/internal_audit_smoke.py` |

### Lista B F26 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F26: **0.18.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 27 — qué auditar (existe en repo)

| Doc | Path |
|-----|------|
| Spec / DoD | `docs/FASE_27_STRATEGY_CATALOG.md` |
| Implementation report | `docs/audit/FASE_27_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F27.md` |
| Review Package INTERNAL | `docs/audit/FASE_27_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F27.md` |
| Noche F19–F27 | `docs/audit/INTERNAL_AUDIT_F19_F27_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 27** |

**Certificado externo:** **NO** emitido (`FASE_27_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F27 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Catálogo + factory + MM adapter | `workbench/strategy_catalog.py` |
| A2 | Wire paper session + lab | `paper_session.py` · `lab_services.py` |
| A3 | `GET /api/lab/strategies` | `api.py` + `server.py` |
| A4 | UI selectores + params | `static/js/panes/paper_session.js`, `backtest.js` |
| A5 | LIVE gate + PaperBroker-only | `execution/live_gate.py` · runner isinstance |
| A6 | DEC-071 | `learning/decisiones.txt` |
| A7 | Suite F27 | `tests/unit/workbench/test_strategy_catalog_f27.py` |
| A8 | Smoke F27 | `scripts/internal_audit_smoke.py` |

### Lista B F27 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F27: **0.19.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 28 — Layout Persistence + Journal Viewer

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_28_LAYOUT_JOURNAL.md` |
| Implementation report | `docs/audit/FASE_28_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F28.md` |
| Review Package INTERNAL | `docs/audit/FASE_28_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F28.md` |
| Noche F19–F28 | `docs/audit/INTERNAL_AUDIT_F19_F28_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 28** |

**Certificado externo:** **NO** emitido (`FASE_28_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F28 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Layout save/load | `workbench/layout.py` |
| A2 | `GET`/`PUT` `/api/layout` | `api.py` + `server.py` |
| A3 | WM debounce + restore | `static/js/wm.js`, `shell.js` |
| A4 | Panel Journal + CSV | `static/js/panes/journal.js` |
| A5 | LIVE gate | `execution/live_gate.py` |
| A6 | DEC-072 | `learning/decisiones.txt` |
| A7 | Suite F28 | `tests/unit/workbench/test_layout_f28.py` |
| A8 | Smoke F28 | `scripts/internal_audit_smoke.py` |

### Lista B F28 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F28: **0.20.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 29 — Report Viewer + Metrics History

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_29_REPORTS.md` |
| Implementation report | `docs/audit/FASE_29_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F29.md` |
| Review Package INTERNAL | `docs/audit/FASE_29_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F29.md` |
| Noche F19–F29 | `docs/audit/INTERNAL_AUDIT_F19_F29_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 29** |

**Certificado externo:** **NO** emitido (`FASE_29_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F29 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Persist reports | `workbench/reports.py` |
| A2 | Session `reports_dir` | `workbench/session.py` |
| A3 | Backtest wire | `lab_services.run_lab_backtest` |
| A4 | `GET /api/lab/reports` + `/{id}` | `api.py` + `server.py` |
| A5 | Panel Reports | `static/js/panes/reports.js` |
| A6 | LIVE gate | `execution/live_gate.py` |
| A7 | DEC-073 | `learning/decisiones.txt` |
| A8 | Suite F29 | `tests/unit/workbench/test_reports_f29.py` |
| A9 | Smoke F29 | `scripts/internal_audit_smoke.py` |

### Lista B F29 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F29: **0.21.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 30 — Universe Watchlist + Data Catalog Browser

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_30_UNIVERSE_CATALOG.md` |
| Implementation report | `docs/audit/FASE_30_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F30.md` |
| Review Package INTERNAL | `docs/audit/FASE_30_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F30.md` |
| Noche F19–F30 | `docs/audit/INTERNAL_AUDIT_F19_F30_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 30** |

**Certificado externo:** **NO** emitido (`FASE_30_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F30 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Watchlist persist | `workbench/watchlist.py` |
| A2 | Catalog browser | `workbench/catalog_browser.py` |
| A3 | Session `watchlist_path` | `workbench/session.py` |
| A4 | `GET`/`PUT` `/api/watchlist` + universe/catalog | `api.py` + `server.py` |
| A5 | Paneles Universe + Catalog | `static/js/panes/universe.js` · `catalog.js` |
| A6 | LIVE gate | `execution/live_gate.py` |
| A7 | DEC-074 | `learning/decisiones.txt` |
| A8 | Suite F30 | `tests/unit/workbench/test_universe_catalog_f30.py` |
| A9 | Smoke F30 | `scripts/internal_audit_smoke.py` |

### Lista B F30 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F30: **0.22.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 31 — Feature Store Browser + Pipeline Runner UI

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_31_FEATURES_UI.md` |
| Implementation report | `docs/audit/FASE_31_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F31.md` |
| Review Package INTERNAL | `docs/audit/FASE_31_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F31.md` |
| Noche F19–F31 | `docs/audit/INTERNAL_AUDIT_F19_F31_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 31** |

**Certificado externo:** **NO** emitido (`FASE_31_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F31 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Feature store browser | `workbench/feature_store_browser.py` |
| A2 | Session `features_dir` | `workbench/session.py` |
| A3 | Lab persist `FeatureStore.put` | `workbench/lab_services.py` |
| A4 | `GET` store + `POST` run | `api.py` + `server.py` |
| A5 | Panel Features enriquecido | `static/js/panes/features.js` |
| A6 | LIVE gate | `execution/live_gate.py` |
| A7 | DEC-075 | `learning/decisiones.txt` |
| A8 | Suite F31 | `tests/unit/workbench/test_features_store_f31.py` |
| A9 | Smoke F31 | `scripts/internal_audit_smoke.py` |

### Lista B F31 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F31: **0.23.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 32 — Validation / Walk-Forward Runner UI

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_32_VALIDATION_UI.md` |
| Implementation report | `docs/audit/FASE_32_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F32.md` |
| Review Package INTERNAL | `docs/audit/FASE_32_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F32.md` |
| Noche F19–F32 | `docs/audit/INTERNAL_AUDIT_F19_F32_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 32** |

**Certificado externo:** **NO** emitido (`FASE_32_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F32 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Persist validation runs | `workbench/validation_runs.py` |
| A2 | Session `validation_dir` | `workbench/session.py` |
| A3 | Lab runner índices + leakage | `workbench/lab_services.py` |
| A4 | `POST` run + `GET` list/get | `api.py` + `server.py` |
| A5 | Panel Validation enriquecido | `static/js/panes/validation.js` |
| A6 | LIVE gate | `execution/live_gate.py` |
| A7 | DEC-076 | `learning/decisiones.txt` |
| A8 | Suite F32 | `tests/unit/workbench/test_validation_f32.py` |
| A9 | Smoke F32 | `scripts/internal_audit_smoke.py` |

### Lista B F32 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F32: **0.24.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 33 — Optimizer History + Pareto Panel (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.25.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** historial de optimize lab runs en session `optimizer/` + frente Pareto simple (sharpe↑/MDD↓) + panel UI.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_33_OPTIMIZER_UI.md` |
| Implementation report | `docs/audit/FASE_33_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F33.md` |
| Review Package INTERNAL | `docs/audit/FASE_33_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F33.md` |
| Noche F19–F33 | `docs/audit/INTERNAL_AUDIT_F19_F33_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 33** |

**Certificado externo:** **NO** emitido (`FASE_33_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F33 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Persist optimizer runs | `workbench/optimizer_runs.py` |
| A2 | Session `optimizer_dir` | `workbench/session.py` |
| A3 | Lab runner grid + Pareto | `workbench/lab_services.py` |
| A4 | `POST` optimize + `GET` history | `api.py` + `server.py` |
| A5 | Panel Optimizer enriquecido | `static/js/panes/optimize.js` |
| A6 | LIVE gate | `execution/live_gate.py` |
| A7 | DEC-077 | `learning/decisiones.txt` |
| A8 | Suite F33 | `tests/unit/workbench/test_optimizer_f33.py` |
| A9 | Smoke F33 | `scripts/internal_audit_smoke.py` |

### Lista B F33 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F33: **0.25.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 34 — Monte Carlo History + Hummingbot Export Wizard (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.26.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** historial Monte Carlo en session `montecarlo/` + intervalos CI; wizard Hummingbot export (experiments → validate/build/export) + `GET /api/lab/exports` + banner `live_routing:false`.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_34_MC_EXPORT.md` |
| Implementation report | `docs/audit/FASE_34_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F34.md` |
| Review Package INTERNAL | `docs/audit/FASE_34_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F34.md` |
| Noche F19–F34 | `docs/audit/INTERNAL_AUDIT_F19_F34_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 34** |

**Certificado externo:** **NO** emitido (`FASE_34_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F34 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Persist MC runs | `workbench/montecarlo_runs.py` |
| A2 | List HB exports | `workbench/hb_exports.py` |
| A3 | Session `montecarlo_dir` | `workbench/session.py` |
| A4 | Lab runners MC + export | `workbench/lab_services.py` |
| A5 | API history + exports | `api.py` + `server.py` |
| A6 | Panel MC enriquecido | `static/js/panes/montecarlo.js` |
| A7 | Panel Export wizard | `static/js/panes/export_hb.js` |
| A8 | LIVE gate | `execution/live_gate.py` |
| A9 | DEC-078 | `learning/decisiones.txt` |
| A10 | Suite F34 | `tests/unit/workbench/test_mc_export_f34.py` |
| A11 | Smoke F34 | `scripts/internal_audit_smoke.py` |

### Lista B F34 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F34: **0.26.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Mensaje corto para el auditor

1. F0–F18 certificado formal externo; F19–F34 **APROBADO_INTERNO**.  
2. QuantLab v0.26.0: Monte Carlo History + Hummingbot Export Wizard.  
3. **LIVE sigue BLOQUEADO**; MC/export persist path-safe; export `live_routing:false`.  
4. Arcos F19–F22 + F23–F25 + noche F19–F34 INTERNAL.  
5. **No** emitir `FASE_*_APPROVED.md` desde INTERNAL.
