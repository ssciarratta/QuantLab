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

## Fase 35 — Command Palette + Keyboard Shortcuts (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.27.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** command palette Windows-like (`Ctrl+K` / `Ctrl+Shift+P`) + atajos Ctrl+1..9 / Esc / Ctrl+W; `GET /api/commands` con paneles + acciones seguras (health refresh — sin LIVE).

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_35_COMMAND_PALETTE.md` |
| Implementation report | `docs/audit/FASE_35_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F35.md` |
| Review Package INTERNAL | `docs/audit/FASE_35_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F35.md` |
| Noche F19–F35 | `docs/audit/INTERNAL_AUDIT_F19_F35_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 35** |

**Certificado externo:** **NO** emitido (`FASE_35_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F35 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Registry comandos | `workbench/commands.py` |
| A2 | API GET /api/commands | `api.py` + `server.py` |
| A3 | Command palette JS | `static/js/command_palette.js` |
| A4 | Shell shortcuts | `static/js/shell.js` |
| A5 | WM closeFocused | `static/js/wm.js` |
| A6 | CSS palette | `static/css/workbench.css` |
| A7 | LIVE gate | `execution/live_gate.py` |
| A8 | DEC-079 | `learning/decisiones.txt` |
| A9 | Suite F35 | `tests/unit/workbench/test_commands_f35.py` |
| A10 | Smoke F35 | `scripts/internal_audit_smoke.py` |

### Lista B F35 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F35: **0.27.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 36 — Settings + Status Bar (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.28.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** settings.json por sesión (theme, default_venue, default_strategy, slippage_bps, locale=es) + `GET/PUT /api/settings` + panel Settings + status bar fija inferior (mode, live_blocked, session_id, venue, md_provider, clock).

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_36_SETTINGS.md` |
| Implementation report | `docs/audit/FASE_36_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F36.md` |
| Review Package INTERNAL | `docs/audit/FASE_36_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F36.md` |
| Noche F19–F36 | `docs/audit/INTERNAL_AUDIT_F19_F36_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 36** |

**Certificado externo:** **NO** emitido (`FASE_36_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F36 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Persistencia | `workbench/settings.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Panel Settings | `static/js/panes/settings.js` |
| A4 | Status bar | `static/index.html` · `shell.js` · CSS |
| A5 | Spec | `docs/FASE_36_SETTINGS.md` |
| A6 | Implementation report | `docs/audit/FASE_36_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-080 | `learning/decisiones.txt` |
| A8 | Suite F36 | `tests/unit/workbench/test_settings_f36.py` |
| A9 | Version 0.28.0 | `pyproject.toml` |

### Lista B F36 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F36: **0.28.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 37 — First-run Onboarding Wizard (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.29.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** wizard modal first-run si `meta.onboarding_done` ausente; 4 pasos (TESTER/REAL/LIVE bloqueado → venue tester → Paper/Backtest → Chat IA safe); `GET /api/onboarding` + `POST /api/onboarding/complete`.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_37_ONBOARDING.md` |
| Implementation report | `docs/audit/FASE_37_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F37.md` |
| Review Package INTERNAL | `docs/audit/FASE_37_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F37.md` |
| Noche F19–F37 | `docs/audit/INTERNAL_AUDIT_F19_F37_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 37** |

**Certificado externo:** **NO** emitido (`FASE_37_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F37 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Persistencia | `workbench/onboarding.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Wizard JS | `static/js/onboarding.js` |
| A4 | Boot + CSS | `shell.js` · `api.js` · `index.html` · CSS |
| A5 | Spec | `docs/FASE_37_ONBOARDING.md` |
| A6 | Implementation report | `docs/audit/FASE_37_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-081 | `learning/decisiones.txt` |
| A8 | Suite F37 | `tests/unit/workbench/test_onboarding_f37.py` |
| A9 | Version 0.29.0 | `pyproject.toml` |

### Lista B F37 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F37: **0.29.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 38 — Docs / Help Browser (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.30.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** browser Help/Docs read-only sobre `docs/*.md` + `docs/ops/*.md`; `GET /api/docs` + `GET /api/docs/content?path=` fail-closed; panel buscar + preview HTML escapado|pre; chat `search_docs` incluye ops/.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_38_DOCS_HELP.md` |
| Implementation report | `docs/audit/FASE_38_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F38.md` |
| Review Package INTERNAL | `docs/audit/FASE_38_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F38.md` |
| Noche F19–F38 | `docs/audit/INTERNAL_AUDIT_F19_F38_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 38** |

**Certificado externo:** **NO** emitido (`FASE_38_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F38 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Browser | `workbench/docs_browser.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Panel Docs | `static/js/panes/docs.js` |
| A4 | Shell / menu / CSS | `shell.js` · `api.js` · `index.html` · CSS |
| A5 | Spec | `docs/FASE_38_DOCS_HELP.md` |
| A6 | Implementation report | `docs/audit/FASE_38_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-082 | `learning/decisiones.txt` |
| A8 | Suite F38 | `tests/unit/workbench/test_docs_f38.py` |
| A9 | Version 0.30.0 | `pyproject.toml` |

### Lista B F38 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F38: **0.30.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 39 — Session Export/Import ZIP (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.31.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** export/import del directorio durable de sesión como ZIP research-safe (sin secretos); `GET /api/session/export` (+ download) + `POST /api/session/import` (`new`|`merge` fail-closed); zip-slip vía `scale.backup`; UI en Settings.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_39_SESSION_ZIP.md` |
| Implementation report | `docs/audit/FASE_39_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F39.md` |
| Review Package INTERNAL | `docs/audit/FASE_39_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F39.md` |
| Noche F19–F39 | `docs/audit/INTERNAL_AUDIT_F19_F39_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 39** |

**Certificado externo:** **NO** emitido (`FASE_39_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F39 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Session ZIP | `workbench/session_zip.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Settings UI Export/Import | `static/js/panes/settings.js` |
| A4 | API client | `static/js/api.js` |
| A5 | Spec | `docs/FASE_39_SESSION_ZIP.md` |
| A6 | Implementation report | `docs/audit/FASE_39_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-083 | `learning/decisiones.txt` |
| A8 | Suite F39 | `tests/unit/workbench/test_session_zip_f39.py` |
| A9 | Version 0.31.0 | `pyproject.toml` |

### Lista B F39 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F39: **0.31.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 40 — Workspace Presets (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.32.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** presets MDI built-in (`research` / `trading_paper` / `ops`); `GET /api/presets` + `POST /api/presets/apply` reescribe `layout.json`; UI menú Inicio → Espacios de trabajo.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_40_PRESETS.md` |
| Implementation report | `docs/audit/FASE_40_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F40.md` |
| Review Package INTERNAL | `docs/audit/FASE_40_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F40.md` |
| Noche F19–F40 | `docs/audit/INTERNAL_AUDIT_F19_F40_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 40** |

**Certificado externo:** **NO** emitido (`FASE_40_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F40 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | Presets | `workbench/presets.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | Start menu Espacios | `static/index.html` · `shell.js` |
| A4 | API client | `static/js/api.js` |
| A5 | Spec | `docs/FASE_40_PRESETS.md` |
| A6 | Implementation report | `docs/audit/FASE_40_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-084 | `learning/decisiones.txt` |
| A8 | Suite F40 | `tests/unit/workbench/test_presets_f40.py` |
| A9 | Version 0.32.0 | `pyproject.toml` |

### Lista B F40 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F40: **0.32.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Mensaje corto para el auditor

1. F0–F18 certificado formal externo; F19–F47 **APROBADO_INTERNO**.  
2. QuantLab v0.39.0: Chat Context Awareness.  
3. **LIVE sigue BLOQUEADO**; chat sin trading tools.  
4. Arcos F19–F22 + F23–F25 + noche F19–F47 INTERNAL.  
5. **No** emitir `FASE_*_APPROVED.md` desde INTERNAL.

---

## Fase 45 — About Dialog + Version Badge (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.37.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** `GET /api/about` + badge de versión en status bar + diálogo Acerca de (menú Inicio / command palette); phases_summary tip actual `F19–F47 INTERNAL`; bind_policy loopback-default.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_45_ABOUT.md` |
| Implementation report | `docs/audit/FASE_45_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F45.md` |
| Review Package INTERNAL | `docs/audit/FASE_45_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F45.md` |
| Noche F19–F45 | `docs/audit/INTERNAL_AUDIT_F19_F45_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 45** |

**Certificado externo:** **NO** emitido (`FASE_45_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F45 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | About module | `workbench/about.py` |
| A2 | API + server | `api.py` · `server.py` |
| A3 | UI About + badge | `about.js` · `shell.js` · `index.html` · CSS |
| A4 | Spec | `docs/FASE_45_ABOUT.md` |
| A5 | Implementation report | `docs/audit/FASE_45_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-089 | `learning/decisiones.txt` |
| A7 | Suite F45 | `tests/unit/workbench/test_about_f45.py` |
| A8 | Version 0.37.0 | `pyproject.toml` |

### Lista B F45 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F45: **0.37.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 46 — Multi-Session Switcher (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.38.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** `GET /api/sessions` + `POST /api/sessions/switch` + `POST /api/sessions/new`; UI panel Sessions; fail-closed `validate_session_id`; recrea paths journal/book/labs.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_46_SESSIONS.md` |
| Implementation report | `docs/audit/FASE_46_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F46.md` |
| Review Package INTERNAL | `docs/audit/FASE_46_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F46.md` |
| Noche F19–F46 | `docs/audit/INTERNAL_AUDIT_F19_F46_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 46** |

**Certificado externo:** **NO** emitido (`FASE_46_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F46 (entregables)

| ID | Entregable | Path |
|----|------------|------|
| A1 | list_sessions + validate | `workbench/session.py` |
| A2 | WorkbenchState switch/new + API | `api.py` · `server.py` |
| A3 | UI Sessions panel | `sessions.js` · `shell.js` · `index.html` · CSS |
| A4 | Spec | `docs/FASE_46_SESSIONS.md` |
| A5 | Implementation report | `docs/audit/FASE_46_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-090 | `learning/decisiones.txt` |
| A7 | Suite F46 | `tests/unit/workbench/test_sessions_f46.py` |
| A8 | Version 0.38.0 | `pyproject.toml` |

### Lista B F46 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F46: **0.38.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 47 — Chat Context Awareness (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.39.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** Extiende chat allowlist read-only con `get_session_summary` (mode/venue/equity/posiciones/activity), `list_reports`, `list_strategies`; FakeProvider intents ES; chat **sin** trading tools.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_47_CHAT_CONTEXT.md` |
| Implementation report | `docs/audit/FASE_47_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F47.md` |
| Review Package INTERNAL | `docs/audit/FASE_47_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F47.md` |
| Noche F19–F47 | `docs/audit/INTERNAL_AUDIT_F19_F47_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 47** |

**Certificado externo:** **NO** emitido (`FASE_47_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F47 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Allowlist + handlers | `workbench/chat/tools.py` |
| A2 | FakeProvider ES | `workbench/chat/providers.py` |
| A3 | Spec | `docs/FASE_47_CHAT_CONTEXT.md` |
| A4 | Implementation report | `docs/audit/FASE_47_IMPLEMENTATION_REPORT.md` |
| A5 | DEC-091 | `learning/decisiones.txt` |
| A6 | Suite F47 | `tests/unit/workbench/test_chat_context_f47.py` |
| A7 | Smoke F47 | `scripts/internal_audit_smoke.py` |
| A8 | Version 0.39.0 | `pyproject.toml` |

### Lista B F47 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F47: **0.39.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 48 — Theme CSS Completion (Workbench)

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.40.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** Completa tokens CSS para themes `slate` | `high-contrast` (chrome + semantic); `data-theme` en `documentElement` al load/PUT settings; settings roundtrip.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_48_THEMES.md` |
| Implementation report | `docs/audit/FASE_48_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F48.md` |
| Review Package INTERNAL | `docs/audit/FASE_48_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F48.md` |
| Noche F19–F48 | `docs/audit/INTERNAL_AUDIT_F19_F48_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 48** |

**Certificado externo:** **NO** emitido (`FASE_48_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F48 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Tokens CSS | `static/css/workbench.css` |
| A2 | data-theme apply | `index.html` · `shell.js` · `settings.js` |
| A3 | Spec | `docs/FASE_48_THEMES.md` |
| A4 | Implementation report | `docs/audit/FASE_48_IMPLEMENTATION_REPORT.md` |
| A5 | DEC-092 | `learning/decisiones.txt` |
| A6 | Suite F48 | `tests/unit/workbench/test_themes_f48.py` |
| A7 | Smoke F48 | `scripts/internal_audit_smoke.py` |
| A8 | Version 0.40.0 | `pyproject.toml` |

### Lista B F48 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F48: **0.40.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 49 — Milestone Freeze Docs + CHANGELOG Sync

**Estado:** 📦 ✅ **APROBADO_INTERNO** (2026-07-26)  
**Código:** 0.41.0 · branch `cursor/modo-real-workbench-aafd`  
**LIVE:** BLOQUEADO · flip **NO**

**Qué es:** Freeze documental del milestone workbench F19–F48 (v0.40.0): inventario, invariantes, cómo operar, límites (no LIVE); sync CHANGELOG/RESUMEN/PROJECT_MEMORY/README; smoke About≡`__version__`; bundle F19–F49.

**Docs de auditoría:**

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_49_MILESTONE.md` |
| Implementation report | `docs/audit/FASE_49_IMPLEMENTATION_REPORT.md` |
| Freeze | `docs/audit/MILESTONE_V040_FREEZE.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F49.md` |
| Review Package INTERNAL | `docs/audit/FASE_49_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F49.md` |
| Noche F19–F49 | `docs/audit/INTERNAL_AUDIT_F19_F49_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 49** |

**Certificado externo:** **NO** emitido (`FASE_49_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F49 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Milestone freeze | `docs/audit/MILESTONE_V040_FREEZE.md` |
| A2 | Spec | `docs/FASE_49_MILESTONE.md` |
| A3 | Implementation report | `docs/audit/FASE_49_IMPLEMENTATION_REPORT.md` |
| A4 | DEC-093 | `learning/decisiones.txt` |
| A5 | CHANGELOG sync | `CHANGELOG.md` |
| A6 | Tip sync | `RESUMEN_PROYECTO.txt` · `.cursor/PROJECT_MEMORY.md` · `README.md` |
| A7 | Smoke About version | `scripts/internal_audit_smoke.py` |
| A8 | Bundle to-phase 49 | `scripts/build_internal_review_bundle.py` |
| A9 | Version 0.41.0 | `pyproject.toml` |

### Lista B F49 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F49: **0.41.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 50 — Performance Baseline Workbench API

**Código:** 0.42.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-094  
**Qué es:** Baseline de latencia loopback para endpoints clave del workbench API (health, mode, commands, about, lab/capabilities); assert p95/max < 500ms; CLI + suite; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_50_PERF_BASELINE.md` |
| Implementation report | `docs/audit/FASE_50_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F50.md` |
| Review Package INTERNAL | `docs/audit/FASE_50_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F50.md` |
| Noche F19–F50 | `docs/audit/INTERNAL_AUDIT_F19_F50_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 50** |

**Certificado externo:** **NO** emitido (`FASE_50_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F50 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Módulo perf_baseline | `src/quantlab/workbench/perf_baseline.py` |
| A2 | Suite F50 | `tests/unit/workbench/test_perf_baseline_f50.py` |
| A3 | CLI baseline | `scripts/workbench_perf_baseline.py` |
| A4 | Spec | `docs/FASE_50_PERF_BASELINE.md` |
| A5 | Implementation report | `docs/audit/FASE_50_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-094 | `learning/decisiones.txt` |
| A7 | Smoke F50 | `scripts/internal_audit_smoke.py` |
| A8 | Bundle to-phase 50 | `scripts/build_internal_review_bundle.py` |
| A9 | Version 0.42.0 | `pyproject.toml` |

### Lista B F50 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
uv run python scripts/workbench_perf_baseline.py
```

Versión código F50: **0.42.0** · LIVE: **BLOQUEADO** · flip: **NO**.
