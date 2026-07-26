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

---

## Fase 51 — API Rate Limit (loopback soft)

**Código:** 0.43.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-095  
**Qué es:** Soft rate limit in-process del workbench HTTP (token bucket por IP+path); default 120 req/s; 429 JSON + Retry-After; tests con límite bajo inyectado; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_51_RATE_LIMIT.md` |
| Implementation report | `docs/audit/FASE_51_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F51.md` |
| Review Package INTERNAL | `docs/audit/FASE_51_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F51.md` |
| Noche F19–F51 | `docs/audit/INTERNAL_AUDIT_F19_F51_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 51** |

**Certificado externo:** **NO** emitido (`FASE_51_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F51 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Módulo rate_limit | `src/quantlab/workbench/rate_limit.py` |
| A2 | Suite F51 | `tests/unit/workbench/test_rate_limit_f51.py` |
| A3 | Spec | `docs/FASE_51_RATE_LIMIT.md` |
| A4 | Implementation report | `docs/audit/FASE_51_IMPLEMENTATION_REPORT.md` |
| A5 | DEC-095 | `learning/decisiones.txt` |
| A6 | Smoke F51 | `scripts/internal_audit_smoke.py` |
| A7 | Bundle to-phase 51 | `scripts/build_internal_review_bundle.py` |
| A8 | Version 0.43.0 | `pyproject.toml` |

### Lista B F51 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F51: **0.43.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 52 — Graceful Shutdown + Paper Session Safety

**Código:** 0.44.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-096  
**Qué es:** Apagado ordenado del workbench (SIGINT/SIGTERM + `POST /api/shutdown` loopback): detiene paper session runner, flushea layout/settings/book y apaga el HTTPServer; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_52_SHUTDOWN.md` |
| Implementation report | `docs/audit/FASE_52_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F52.md` |
| Review Package INTERNAL | `docs/audit/FASE_52_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F52.md` |
| Noche F19–F52 | `docs/audit/INTERNAL_AUDIT_F19_F52_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 52** |

**Certificado externo:** **NO** emitido (`FASE_52_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F52 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Módulo shutdown | `src/quantlab/workbench/shutdown.py` |
| A2 | Suite F52 | `tests/unit/workbench/test_shutdown_f52.py` |
| A3 | Spec | `docs/FASE_52_SHUTDOWN.md` |
| A4 | Implementation report | `docs/audit/FASE_52_IMPLEMENTATION_REPORT.md` |
| A5 | DEC-096 | `learning/decisiones.txt` |
| A6 | Smoke F52 | `scripts/internal_audit_smoke.py` |
| A7 | Bundle to-phase 52 | `scripts/build_internal_review_bundle.py` |
| A8 | Version 0.44.0 | `pyproject.toml` |

### Lista B F52 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F52: **0.44.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 53 — Dockerfile Workbench (opt-in)

**Código:** 0.45.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-097  
**Qué es:** Imagen Docker opt-in del Workbench (`Dockerfile.workbench`: python 3.12-slim + uv sync; CMD `--host 0.0.0.0 --allow-non-loopback --no-browser`); publish seguro `-p 127.0.0.1:8765:8765`; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_53_DOCKER.md` |
| Ops | `docs/ops/DOCKER_WORKBENCH.md` |
| Implementation report | `docs/audit/FASE_53_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F53.md` |
| Review Package INTERNAL | `docs/audit/FASE_53_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F53.md` |
| Noche F19–F53 | `docs/audit/INTERNAL_AUDIT_F19_F53_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 53** |

**Certificado externo:** **NO** emitido (`FASE_53_APPROVED.md` ausente a propósito).  
**INTERNAL:** **APROBADO_INTERNO** (2026-07-26).

### Lista A F53 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Dockerfile | `Dockerfile.workbench` |
| A2 | Dockerignore | `.dockerignore` |
| A3 | Ops guide | `docs/ops/DOCKER_WORKBENCH.md` |
| A4 | Suite F53 | `tests/unit/workbench/test_dockerfile_f53.py` |
| A5 | Spec | `docs/FASE_53_DOCKER.md` |
| A6 | Implementation report | `docs/audit/FASE_53_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-097 | `learning/decisiones.txt` |
| A8 | Smoke F53 | `scripts/internal_audit_smoke.py` |
| A9 | Bundle to-phase 53 | `scripts/build_internal_review_bundle.py` |
| A10 | Version 0.45.0 | `pyproject.toml` |

### Lista B F53 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F53: **0.45.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 54 — Readiness / Liveness Probes

**Código:** 0.46.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-098  
**Qué es:** Probes HTTP `GET /api/livez` (liveness 200) y `GET /api/readyz` (200 si LIVE_BLOCKED + session root writable; 503 si no); ops HEALTHCHECK en Docker; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_54_PROBES.md` |
| Ops | `docs/ops/DOCKER_WORKBENCH.md` (sección probes) |
| Implementation report | `docs/audit/FASE_54_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F54.md` |
| Review Package INTERNAL | `docs/audit/FASE_54_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F54.md` |
| Noche F19–F54 | `docs/audit/INTERNAL_AUDIT_F19_F54_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 54** |

**Certificado externo:** **NO** emitido (`FASE_54_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F54 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Probes module | `src/quantlab/workbench/probes.py` |
| A2 | API handlers | `handle_get_livez` / `handle_get_readyz` en `api.py` |
| A3 | Server routes | `GET /api/livez` · `GET /api/readyz` |
| A4 | Suite F54 | `tests/unit/workbench/test_probes_f54.py` |
| A5 | Spec | `docs/FASE_54_PROBES.md` |
| A6 | Implementation report | `docs/audit/FASE_54_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-098 | `learning/decisiones.txt` |
| A8 | Smoke F54 | `scripts/internal_audit_smoke.py` |
| A9 | Bundle to-phase 54 | `scripts/build_internal_review_bundle.py` |
| A10 | Version 0.46.0 | `pyproject.toml` |

### Lista B F54 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F54: **0.46.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 55 — OpenAPI / API Catalog

**Código:** 0.47.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-099  
**Qué es:** `GET /api/openapi.json` — schema OpenAPI 3 mínimo generado desde catálogo estático `api_catalog` (paths/methods/summary; sin FastAPI); sin rutas LIVE trading; link About opcional.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_55_OPENAPI.md` |
| Implementation report | `docs/audit/FASE_55_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F55.md` |
| Review Package INTERNAL | `docs/audit/FASE_55_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F55.md` |
| Noche F19–F55 | `docs/audit/INTERNAL_AUDIT_F19_F55_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 55** |

**Certificado externo:** **NO** emitido (`FASE_55_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F55 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | API catalog module | `src/quantlab/workbench/api_catalog.py` |
| A2 | API handler | `handle_get_openapi` en `api.py` |
| A3 | Server route | `GET /api/openapi.json` |
| A4 | Suite F55 | `tests/unit/workbench/test_openapi_f55.py` |
| A5 | Spec | `docs/FASE_55_OPENAPI.md` |
| A6 | Implementation report | `docs/audit/FASE_55_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-099 | `learning/decisiones.txt` |
| A8 | Smoke F55 | `scripts/internal_audit_smoke.py` |
| A9 | Bundle to-phase 55 | `scripts/build_internal_review_bundle.py` |
| A10 | Version 0.47.0 | `pyproject.toml` |

### Lista B F55 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F55: **0.47.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 56 — Security Headers

**Código:** 0.48.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-100  
**Qué es:** Headers de seguridad en respuestas workbench (`nosniff` / `DENY` / `no-referrer`; `Cache-Control: no-store` en `/api/*`); CORS fail-closed (nunca `ACAO *`; Origin non-loopback no se refleja).

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_56_SECURITY_HEADERS.md` |
| Implementation report | `docs/audit/FASE_56_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F56.md` |
| Review Package INTERNAL | `docs/audit/FASE_56_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F56.md` |
| Noche F19–F56 | `docs/audit/INTERNAL_AUDIT_F19_F56_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 56** |

**Certificado externo:** **NO** emitido (`FASE_56_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F56 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Security headers module | `src/quantlab/workbench/security_headers.py` |
| A2 | Server integration | `_apply_security_headers` en `server.py` |
| A3 | Suite F56 | `tests/unit/workbench/test_security_headers_f56.py` |
| A4 | Spec | `docs/FASE_56_SECURITY_HEADERS.md` |
| A5 | Implementation report | `docs/audit/FASE_56_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-100 | `learning/decisiones.txt` |
| A7 | Smoke F56 | `scripts/internal_audit_smoke.py` |
| A8 | Bundle to-phase 56 | `scripts/build_internal_review_bundle.py` |
| A9 | Version 0.48.0 | `pyproject.toml` |

### Lista B F56 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F56: **0.48.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 57 — Content-Security-Policy

**Código:** 0.49.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-101  
**Qué es:** `Content-Security-Policy` restrictiva para SPA local (`default-src`/`script-src`/`connect-src 'self'`; `style-src 'self' 'unsafe-inline'`; `frame-ancestors 'none'`; sin `unsafe-eval`).

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_57_CSP.md` |
| Implementation report | `docs/audit/FASE_57_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F57.md` |
| Review Package INTERNAL | `docs/audit/FASE_57_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F57.md` |
| Noche F19–F57 | `docs/audit/INTERNAL_AUDIT_F19_F57_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 57** |

**Certificado externo:** **NO** emitido (`FASE_57_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F57 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | CSP en security_headers | `src/quantlab/workbench/security_headers.py` |
| A2 | Server integration | `_apply_security_headers` (hereda SECURITY_HEADERS) |
| A3 | Suite F57 | `tests/unit/workbench/test_csp_f57.py` |
| A4 | Spec | `docs/FASE_57_CSP.md` |
| A5 | Implementation report | `docs/audit/FASE_57_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-101 | `learning/decisiones.txt` |
| A7 | Smoke F57 | `scripts/internal_audit_smoke.py` |
| A8 | Bundle to-phase 57 | `scripts/build_internal_review_bundle.py` |
| A9 | Version 0.49.0 | `pyproject.toml` |

### Lista B F57 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F57: **0.49.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 58 — Milestone Freeze Docs + CHANGELOG Sync (v0.50)

**Código:** 0.50.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-102  
**Qué es:** Freeze documental del hito workbench F19–F57/F58 (v0.50.0): inventario, invariantes, cómo operar, límites (no LIVE); sync CHANGELOG/RESUMEN/PROJECT_MEMORY/README; smoke version starts with 0.50; bundle F19–F58.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_58_MILESTONE_V050.md` |
| Implementation report | `docs/audit/FASE_58_IMPLEMENTATION_REPORT.md` |
| Freeze | `docs/audit/MILESTONE_V050_FREEZE.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F58.md` |
| Review Package INTERNAL | `docs/audit/FASE_58_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F58.md` |
| Noche F19–F58 | `docs/audit/INTERNAL_AUDIT_F19_F58_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 58** |

**Certificado externo:** **NO** emitido (`FASE_58_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F58 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Milestone freeze | `docs/audit/MILESTONE_V050_FREEZE.md` |
| A2 | Spec | `docs/FASE_58_MILESTONE_V050.md` |
| A3 | Implementation report | `docs/audit/FASE_58_IMPLEMENTATION_REPORT.md` |
| A4 | DEC-102 | `learning/decisiones.txt` |
| A5 | Version 0.50.0 | `pyproject.toml` |
| A6 | Smoke version starts with 0.50 | `scripts/internal_audit_smoke.py` |
| A7 | Bundle to-phase 58 | `scripts/build_internal_review_bundle.py` |

### Lista B F58 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F58: **0.50.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 59 — A11y Basics (focus + aria)

**Código:** 0.51.0 · branch `cursor/modo-real-workbench-aafd`  
**Qué es:** Mejoras a11y mínimas en SPA estático: `role=dialog` + `aria-modal` + `aria-label` en Command Palette / About / Onboarding; `aria-label` taskbar; focus trap Tab en palette; skip link «Ir al contenido».

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_59_A11Y.md` |
| Implementation report | `docs/audit/FASE_59_IMPLEMENTATION_REPORT.md` |
| Review package | `docs/audit/FASE_59_REVIEW_PACKAGE.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F59.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F59.md` |
| Noche F19–F59 | `docs/audit/INTERNAL_AUDIT_F19_F59_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 59** |
| DEC | DEC-103 |

### Lista A F59 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Skip link + dialog shells | `static/index.html` |
| A2 | Focus trap palette | `static/js/command_palette.js` |
| A3 | About / onboarding aria | `about.js` · `onboarding.js` |
| A4 | Taskbar aria-label | `wm.js` · `btn-start` |
| A5 | Suite a11y | `tests/unit/workbench/test_a11y_f59.py` |
| A6 | Version 0.51.0 | `pyproject.toml` |

### Lista B F59 (QA)

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F59: **0.51.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 60 — i18n Scaffold (es default)

**Código:** 0.52.0 · branch `cursor/modo-real-workbench-aafd`  
**Qué es:** Scaffold i18n UI: diccionario es (default) + stub en; `QLi18n` en shell al load desde settings.locale; `GET /api/i18n/{locale}` desde static JSON; data-i18n en menú/chrome.

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_60_I18N.md` |
| Implementation report | `docs/audit/FASE_60_IMPLEMENTATION_REPORT.md` |
| Review package | `docs/audit/FASE_60_REVIEW_PACKAGE.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F60.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F60.md` |
| Noche F19–F60 | `docs/audit/INTERNAL_AUDIT_F19_F60_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 60** |
| DEC | DEC-104 |

### Lista A F60 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | i18n.js + JSON | `static/js/i18n.js` · `static/i18n/` |
| A2 | API i18n | `workbench/i18n.py` · `/api/i18n/{locale}` |
| A3 | Shell applyLocale | `shell.js` · `index.html` |
| A4 | Settings locale es\|en | `settings.py` |
| A5 | Suite i18n | `tests/unit/workbench/test_i18n_f60.py` |
| A6 | Version 0.52.0 | `pyproject.toml` |

### Lista B F60 (QA)

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F60: **0.52.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 61 — Workbench Request Access Log

**Código:** 0.53.0 · branch `cursor/modo-real-workbench-aafd`  
**Qué es:** Access log HTTP append-only por sesión (`access.jsonl`: method, path, status, ms) sin bodies/secrets; settings `access_log` default true; `GET /api/access-log?limit=100`; middleware server.

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_61_ACCESS_LOG.md` |
| Implementation report | `docs/audit/FASE_61_IMPLEMENTATION_REPORT.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F61.md` |
| Noche F19–F61 | `docs/audit/INTERNAL_AUDIT_F19_F61_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 61** |
| DEC | DEC-105 |

### Lista A F61 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | AccessLog module | `workbench/access_log.py` |
| A2 | Session + ZIP | `access.jsonl` |
| A3 | Settings toggle | `settings.access_log` |
| A4 | API + middleware | `/api/access-log` · `server.py` |
| A5 | Suite access log | `tests/unit/workbench/test_access_log_f61.py` |
| A6 | Version 0.53.0 | `pyproject.toml` |

### Lista B F61 (QA)

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F61: **0.53.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 62 — Access Log Panel UI

**Código:** 0.54.0 · branch `cursor/modo-real-workbench-aafd`  
**Qué es:** Panel SPA Access Log que consume `GET /api/access-log` (F61); menú Inicio + command palette `open.access_log`; auto-refresh opcional 5s.

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_62_ACCESS_LOG_UI.md` |
| Implementation report | `docs/audit/FASE_62_IMPLEMENTATION_REPORT.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F62.md` |
| Noche F19–F62 | `docs/audit/INTERNAL_AUDIT_F19_F62_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 62** |
| DEC | DEC-106 |

### Lista A F62 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Panel Access Log | `static/js/panes/access_log.js` |
| A2 | Menú + shell | `index.html` · `shell.js` |
| A3 | Command palette | `open.access_log` |
| A4 | Auto-refresh + dispose | checkbox 5s · `wm.close` |
| A5 | Suite UI | `tests/unit/workbench/test_access_log_ui_f62.py` |
| A6 | Version 0.54.0 | `pyproject.toml` |

### Lista B F62 (QA)

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F62: **0.54.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 63 — Session Auto-Backup

**Código:** 0.55.0 · branch `cursor/modo-real-workbench-aafd`  
**Qué es:** Auto-backup opcional de sesión (ZIP research-safe) a `session/backups/` con rotación max 5; settings `auto_backup_minutes` (0=off); `GET /api/backups`.

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_63_AUTO_BACKUP.md` |
| Implementation report | `docs/audit/FASE_63_IMPLEMENTATION_REPORT.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F63.md` |
| Noche F19–F63 | `docs/audit/INTERNAL_AUDIT_F19_F63_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 63** |
| DEC | DEC-107 |

### Lista A F63 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Auto-backup module | `workbench/auto_backup.py` |
| A2 | Settings field | `auto_backup_minutes` |
| A3 | API lista | `GET /api/backups` |
| A4 | Scheduler + shutdown | `server.py` · `shutdown.py` |
| A5 | Suite | `tests/unit/workbench/test_auto_backup_f63.py` |
| A6 | Version 0.55.0 | `pyproject.toml` |

### Lista B F63 (QA)

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F63: **0.55.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 64 — Backups Panel UI

**Código:** 0.56.0 · branch `cursor/modo-real-workbench-aafd`  
**Qué es:** Panel SPA Backups que lista `GET /api/backups` y dispara `POST /api/backups/run` (manual `run_auto_backup`); menú Inicio + command palette `open.backups`.

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_64_BACKUPS_UI.md` |
| Implementation report | `docs/audit/FASE_64_IMPLEMENTATION_REPORT.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F64.md` |
| Noche F19–F64 | `docs/audit/INTERNAL_AUDIT_F19_F64_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 64** |
| DEC | DEC-108 |

### Lista A F64 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Panel Backups | `static/js/panes/backups.js` |
| A2 | POST run API | `/api/backups/run` |
| A3 | Menú + palette | `index.html` · `shell.js` · `open.backups` |
| A4 | i18n + CSS | `pane.backups` · `workbench.css` |
| A5 | Suite UI | `tests/unit/workbench/test_backups_ui_f64.py` |
| A6 | Version 0.56.0 | `pyproject.toml` |

### Lista B F64 (QA)

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F64: **0.56.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 65 — Blotter CSV Server Export

**Código:** 0.57.0 · branch `cursor/modo-real-workbench-aafd`  
**Qué es:** Export server-side `GET /api/paper/fills.csv` (text/csv del journal paper) + botones **Descargar CSV** en Blotter y Journal.

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_65_BLOTTER_CSV.md` |
| Implementation report | `docs/audit/FASE_65_IMPLEMENTATION_REPORT.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F65.md` |
| Noche F19–F65 | `docs/audit/INTERNAL_AUDIT_F19_F65_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 65** |
| DEC | DEC-109 |

### Lista A F65 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | CSV builder | `brokers/paper/journal.py` · `fills_to_csv` |
| A2 | GET fills.csv | `/api/paper/fills.csv` |
| A3 | UI download | `blotter.js` · `journal.js` · `api.js` |
| A4 | Suite | `tests/unit/workbench/test_fills_csv_f65.py` |
| A5 | Version 0.57.0 | `pyproject.toml` |

### Lista B F65 (QA)

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F65: **0.57.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 66 — Equity Curve Snapshot

**Código:** 0.58.0 · branch `cursor/modo-real-workbench-aafd`  
**Qué es:** Snapshot append-only `equity.jsonl` (`ts`,`equity`,`cash`) en fills paper y paper session step; `GET /api/paper/equity`; sparkline + lista en Positions.

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_66_EQUITY.md` |
| Implementation report | `docs/audit/FASE_66_IMPLEMENTATION_REPORT.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F66.md` |
| Noche F19–F66 | `docs/audit/INTERNAL_AUDIT_F19_F66_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 66** |
| DEC | DEC-110 |

### Lista A F66 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | EquityCurveLog | `workbench/equity_curve.py` |
| A2 | GET equity | `/api/paper/equity` |
| A3 | UI Positions | `positions.js` · sparkline SVG |
| A4 | Suite | `tests/unit/workbench/test_equity_curve_f66.py` |
| A5 | Version 0.58.0 | `pyproject.toml` |

### Lista B F66 (QA)

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F66: **0.58.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 67 — Paper PnL Summary

**Código:** 0.59.0 · branch `cursor/modo-real-workbench-aafd`  
**Qué es:** Resumen PnL paper (realized/unrealized/equity/cash) desde `PaperBook` + marks; `GET /api/paper/pnl`; headers en Positions y Blotter.

| Artefacto | Path |
|-----------|------|
| Spec | `docs/FASE_67_PNL.md` |
| Implementation report | `docs/audit/FASE_67_IMPLEMENTATION_REPORT.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F67.md` |
| Noche F19–F67 | `docs/audit/INTERNAL_AUDIT_F19_F67_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 67** |
| DEC | DEC-111 |

### Lista A F67 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | PaperBook.get_pnl | `brokers/paper/book.py` |
| A2 | GET pnl | `/api/paper/pnl` · `paper_pnl.py` |
| A3 | UI headers | `positions.js` · `blotter.js` |
| A4 | Suite | `tests/unit/workbench/test_paper_pnl_f67.py` |
| A5 | Version 0.59.0 | `pyproject.toml` |

### Lista B F67 (QA)

```bash
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F67: **0.59.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 68 — Milestone Freeze Docs + CHANGELOG Sync (v0.60)

**Código:** 0.60.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-112  
**Qué es:** Freeze documental del hito workbench F19–F67/F68 (v0.60.0): inventario, invariantes, cómo operar, límites (no LIVE); sync CHANGELOG/RESUMEN/PROJECT_MEMORY/README; smoke version starts with 0.60; bundle F19–F68.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_68_MILESTONE_V060.md` |
| Implementation report | `docs/audit/FASE_68_IMPLEMENTATION_REPORT.md` |
| Freeze | `docs/audit/MILESTONE_V060_FREEZE.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F68.md` |
| Review Package INTERNAL | `docs/audit/FASE_68_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F68.md` |
| Noche F19–F68 | `docs/audit/INTERNAL_AUDIT_F19_F68_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 68** |

**Certificado externo:** **NO** emitido (`FASE_68_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F68 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Milestone freeze | `docs/audit/MILESTONE_V060_FREEZE.md` |
| A2 | Spec | `docs/FASE_68_MILESTONE_V060.md` |
| A3 | Implementation report | `docs/audit/FASE_68_IMPLEMENTATION_REPORT.md` |
| A4 | DEC-112 | `learning/decisiones.txt` |
| A5 | Version 0.60.0 | `pyproject.toml` |
| A6 | Smoke version starts with 0.60 | `scripts/internal_audit_smoke.py` |
| A7 | Bundle to-phase 68 | `scripts/build_internal_review_bundle.py` |

### Lista B F68 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F68: **0.60.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 69 — Risk Utilization Report

**Código:** 0.61.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-113  
**Qué es:** Report % used de `max_qty` / `max_notional` vs book/posiciones paper; `GET /api/risk/utilization`; sección Utilización en panel Risk; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_69_RISK_UTIL.md` |
| Implementation report | `docs/audit/FASE_69_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F69.md` |
| Review Package INTERNAL | `docs/audit/FASE_69_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F69.md` |
| Noche F19–F69 | `docs/audit/INTERNAL_AUDIT_F19_F69_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 69** |

**Certificado externo:** **NO** emitido (`FASE_69_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F69 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | risk_utilization helpers | `workbench/risk_utilization.py` |
| A2 | GET /api/risk/utilization | `api.py` · `server.py` |
| A3 | OpenAPI route | `api_catalog.py` |
| A4 | Risk panel Utilización | `static/js/panes/risk.js` |
| A5 | Spec | `docs/FASE_69_RISK_UTIL.md` |
| A6 | Implementation report | `docs/audit/FASE_69_IMPLEMENTATION_REPORT.md` |
| A7 | DEC-113 | `learning/decisiones.txt` |
| A8 | Version 0.61.0 | `pyproject.toml` |
| A9 | Suite + smoke F69 | `test_risk_utilization_f69.py` · smoke |

### Lista B F69 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F69: **0.61.0** · LIVE: **BLOQUEADO** · flip: **NO**.

## Fase 70 — Paper Kill Switch

**Código:** 0.62.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-114  
**Qué es:** Kill switch paper-only — engage rechaza submit + session step con ValidationError; persist meta; API `/api/paper/kill`; botón rojo Risk/Sesión; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_70_KILL_SWITCH.md` |
| Implementation report | `docs/audit/FASE_70_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F70.md` |
| Review Package INTERNAL | `docs/audit/FASE_70_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F70.md` |
| Noche F19–F70 | `docs/audit/INTERNAL_AUDIT_F19_F70_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 70** |

**Certificado externo:** **NO** emitido (`FASE_70_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F70 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | paper_kill helpers | `workbench/paper_kill.py` |
| A2 | WorkbenchState kill flag | `api.py` |
| A3 | GET/POST /api/paper/kill | `api.py` · `server.py` |
| A4 | OpenAPI routes | `api_catalog.py` |
| A5 | Risk + Sesión Paper UI | `risk.js` · `paper_session.js` |
| A6 | Spec | `docs/FASE_70_KILL_SWITCH.md` |
| A7 | Implementation report | `docs/audit/FASE_70_IMPLEMENTATION_REPORT.md` |
| A8 | DEC-114 | `learning/decisiones.txt` |
| A9 | Version 0.62.0 | `pyproject.toml` |
| A10 | Suite + smoke F70 | `test_paper_kill_f70.py` · smoke |

### Lista B F70 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F70: **0.62.0** · LIVE: **BLOQUEADO** · flip: **NO**.

## Fase 71 — Health Extended + 1000 Tests Milestone

**Código:** 0.63.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-115  
**Qué es:** Extiende `GET /api/health` + `GET /api/about` con flags ops (`paper_kill_engaged`, `auto_backup_minutes`, `access_log`); suite edge cases útiles; hito **≥1000 pytest passed**; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_71_HEALTH_1K.md` |
| Implementation report | `docs/audit/FASE_71_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F71.md` |
| Review Package INTERNAL | `docs/audit/FASE_71_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F71.md` |
| Noche F19–F71 | `docs/audit/INTERNAL_AUDIT_F19_F71_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 71** |

**Certificado externo:** **NO** emitido (`FASE_71_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F71 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Ops flags helper | `api.py` `_workbench_ops_flags` |
| A2 | Health + About payload | `api.py` · `about.py` |
| A3 | Health pane + About UI | `health.js` · `about.js` |
| A4 | Spec | `docs/FASE_71_HEALTH_1K.md` |
| A5 | Implementation report | `docs/audit/FASE_71_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-115 | `learning/decisiones.txt` |
| A7 | Version 0.63.0 | `pyproject.toml` |
| A8 | Suite + smoke F71 | `test_health_extended_f71.py` · smoke |

### Lista B F71 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F71: **0.63.0** · LIVE: **BLOQUEADO** · flip: **NO**.

## Fase 72 — Desktop Notifications Hook

**Código:** 0.64.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-116  
**Qué es:** Settings opt-in `desktop_notifications` (default false); cuando true, JS Notification API en toast errors y paper kill engage, con degradación graceful si el permiso es denegado; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_72_NOTIFICATIONS.md` |
| Implementation report | `docs/audit/FASE_72_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F72.md` |
| Review Package INTERNAL | `docs/audit/FASE_72_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F72.md` |
| Noche F19–F72 | `docs/audit/INTERNAL_AUDIT_F19_F72_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 72** |

**Certificado externo:** **NO** emitido (`FASE_72_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F72 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Settings field | `settings.py` · `api.py` |
| A2 | Settings checkbox | `panes/settings.js` |
| A3 | Notification hook | `toasts.js` · `api.js` · `shell.js` |
| A4 | Spec | `docs/FASE_72_NOTIFICATIONS.md` |
| A5 | Implementation report | `docs/audit/FASE_72_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-116 | `learning/decisiones.txt` |
| A7 | Version 0.64.0 | `pyproject.toml` |
| A8 | Suite + smoke F72 | `test_desktop_notifications_f72.py` · smoke |

### Lista B F72 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F72: **0.64.0** · LIVE: **BLOQUEADO** · flip: **NO**.

## Fase 73 — Optional Sound Alerts

**Código:** 0.65.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-117  
**Qué es:** Settings opt-in `sound_alerts` (default false); cuando true, WebAudio beep corto en toast errors y paper kill engage (sin assets externos), con degradación graceful si AudioContext ausente; sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_73_SOUND.md` |
| Implementation report | `docs/audit/FASE_73_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F73.md` |
| Review Package INTERNAL | `docs/audit/FASE_73_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F73.md` |
| Noche F19–F73 | `docs/audit/INTERNAL_AUDIT_F19_F73_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 73** |

**Certificado externo:** **NO** emitido (`FASE_73_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F73 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Settings field | `settings.py` · `api.py` |
| A2 | Settings checkbox | `panes/settings.js` |
| A3 | WebAudio beep hook | `toasts.js` · `shell.js` |
| A4 | Spec | `docs/FASE_73_SOUND.md` |
| A5 | Implementation report | `docs/audit/FASE_73_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-117 | `learning/decisiones.txt` |
| A7 | Version 0.65.0 | `pyproject.toml` |
| A8 | Suite + smoke F73 | `test_sound_alerts_f73.py` · smoke |

### Lista B F73 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F73: **0.65.0** · LIVE: **BLOQUEADO** · flip: **NO**.

## Fase 74 — Status Bar Clock Timezone

**Código:** 0.66.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-118  
**Qué es:** Settings `timezone` (default UTC; opciones UTC|local); status bar clock respeta la preferencia vía JS `toLocaleTimeString` (`timeZone: "UTC"` o local del navegador); sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_74_CLOCK_TZ.md` |
| Implementation report | `docs/audit/FASE_74_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F74.md` |
| Review Package INTERNAL | `docs/audit/FASE_74_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F74.md` |
| Noche F19–F74 | `docs/audit/INTERNAL_AUDIT_F19_F74_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 74** |

**Certificado externo:** **NO** emitido (`FASE_74_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F74 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Settings field | `settings.py` · `api.py` |
| A2 | Settings select | `panes/settings.js` |
| A3 | Status bar clock TZ | `shell.js` |
| A4 | Spec | `docs/FASE_74_CLOCK_TZ.md` |
| A5 | Implementation report | `docs/audit/FASE_74_IMPLEMENTATION_REPORT.md` |
| A6 | DEC-118 | `learning/decisiones.txt` |
| A7 | Version 0.66.0 | `pyproject.toml` |
| A8 | Suite + smoke F74 | `test_clock_timezone_f74.py` · smoke |

### Lista B F74 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F74: **0.66.0** · LIVE: **BLOQUEADO** · flip: **NO**.

## Fase 75 — Broker Heartbeat Status

**Código:** 0.67.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-119  
**Qué es:** `GET /api/broker/heartbeat` llama `broker.health()` si hay broker conectado; si no, `disconnected`. Status bar muestra ok/fail; shell poll cada N=5 s. Sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_75_HEARTBEAT.md` |
| Implementation report | `docs/audit/FASE_75_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F75.md` |
| Review Package INTERNAL | `docs/audit/FASE_75_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F75.md` |
| Noche F19–F75 | `docs/audit/INTERNAL_AUDIT_F19_F75_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 75** |

**Certificado externo:** **NO** emitido (`FASE_75_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F75 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | API heartbeat | `api.py` · `server.py` · `api_catalog.py` |
| A2 | Status bar + poll | `index.html` · `shell.js` · `api.js` |
| A3 | Spec | `docs/FASE_75_HEARTBEAT.md` |
| A4 | Implementation report | `docs/audit/FASE_75_IMPLEMENTATION_REPORT.md` |
| A5 | DEC-119 | `learning/decisiones.txt` |
| A6 | Version 0.67.0 | `pyproject.toml` |
| A7 | Suite + smoke F75 | `test_broker_heartbeat_f75.py` · smoke |

### Lista B F75 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F75: **0.67.0** · LIVE: **BLOQUEADO** · flip: **NO**.

## Fase 76 — Broker Reconnect Button

**Código:** 0.68.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-120  
**Qué es:** `POST /api/broker/reconnect` re-ejecuta los últimos params de connect guardados en session meta (`last_broker_connect`). Connect persiste la config. Botón Reconectar en Market + Health. Sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_76_RECONNECT.md` |
| Implementation report | `docs/audit/FASE_76_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F76.md` |
| Review Package INTERNAL | `docs/audit/FASE_76_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F76.md` |
| Noche F19–F76 | `docs/audit/INTERNAL_AUDIT_F19_F76_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 76** |

**Certificado externo:** **NO** emitido (`FASE_76_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F76 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Persist + reconnect module | `broker_reconnect.py` · `api.py` · `server.py` · `api_catalog.py` |
| A2 | UI Market + Health | `market.js` · `health.js` · `api.js` |
| A3 | Spec | `docs/FASE_76_RECONNECT.md` |
| A4 | Implementation report | `docs/audit/FASE_76_IMPLEMENTATION_REPORT.md` |
| A5 | DEC-120 | `learning/decisiones.txt` |
| A6 | Version 0.68.0 | `pyproject.toml` |
| A7 | Suite + smoke F76 | `test_broker_reconnect_f76.py` · smoke |

### Lista B F76 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F76: **0.68.0** · LIVE: **BLOQUEADO** · flip: **NO**.

## Fase 77 — Broker Disconnect + Milestone prep

**Código:** 0.69.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-121  
**Qué es:** `POST /api/broker/disconnect` cierra el broker y limpia el estado conectado, conservando `last_broker_connect` para reconnect. Botón Desconectar en Market + Health. Prep milestone v0.70. Sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_77_DISCONNECT.md` |
| Implementation report | `docs/audit/FASE_77_IMPLEMENTATION_REPORT.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F77.md` |
| Review Package INTERNAL | `docs/audit/FASE_77_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F77.md` |
| Noche F19–F77 | `docs/audit/INTERNAL_AUDIT_F19_F77_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 77** |

**Certificado externo:** **NO** emitido (`FASE_77_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F77 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Disconnect module + API | `broker_disconnect.py` · `api.py` · `server.py` · `api_catalog.py` |
| A2 | UI Market + Health | `market.js` · `health.js` · `api.js` |
| A3 | Spec | `docs/FASE_77_DISCONNECT.md` |
| A4 | Implementation report | `docs/audit/FASE_77_IMPLEMENTATION_REPORT.md` |
| A5 | DEC-121 | `learning/decisiones.txt` |
| A6 | Version 0.69.0 | `pyproject.toml` |
| A7 | Suite + smoke F77 | `test_broker_disconnect_f77.py` · smoke |

### Lista B F77 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F77: **0.69.0** · LIVE: **BLOQUEADO** · flip: **NO**.

## Fase 78 — Milestone Freeze Docs + CHANGELOG Sync (v0.70)

**Código:** 0.70.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-122  
**Qué es:** Freeze documental del milestone workbench F19–F77/F78 (v0.70.0): inventario, invariantes, cómo operar, límites (no LIVE); sync CHANGELOG/RESUMEN/PROJECT_MEMORY/README; smoke About≡`__version__` startswith 0.70; bundle F19–F78. Sin flip LIVE.

| Doc | Path |
|-----|------|
| Spec | `docs/FASE_78_MILESTONE_V070.md` |
| Implementation report | `docs/audit/FASE_78_IMPLEMENTATION_REPORT.md` |
| Milestone freeze | `docs/audit/MILESTONE_V070_FREEZE.md` |
| Autauditoría | `docs/audit/AUTO_AUDIT_2026-07-26_F78.md` |
| Review Package INTERNAL | `docs/audit/FASE_78_REVIEW_PACKAGE.md` |
| INTERNAL AUDIT | `docs/audit/INTERNAL_AUDIT_F78.md` |
| Noche F19–F78 | `docs/audit/INTERNAL_AUDIT_F19_F78_NIGHT.md` |
| Roadmap | `docs/ROADMAP_ALIGNED.md` → sección **Fase 78** |

**Certificado externo:** **NO** emitido (`FASE_78_APPROVED.md` ausente a propósito).  
**LIVE_BLOCKED:** True (sin flip).

### Lista A F78 (entregables)

| ID | Entrega | Path |
|----|---------|------|
| A1 | Milestone freeze | `docs/audit/MILESTONE_V070_FREEZE.md` |
| A2 | Spec | `docs/FASE_78_MILESTONE_V070.md` |
| A3 | Implementation report | `docs/audit/FASE_78_IMPLEMENTATION_REPORT.md` |
| A4 | DEC-122 | `learning/decisiones.txt` |
| A5 | Version 0.70.0 | `pyproject.toml` |
| A6 | Smoke version starts with 0.70 | `scripts/internal_audit_smoke.py` |
| A7 | Bundle to-phase 78 | `scripts/build_internal_review_bundle.py` |

### Lista B F78 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F78: **0.70.0** · LIVE: **BLOQUEADO** · flip: **NO**.

---

## Fase 79 — Watchlist Import/Export JSON

**Código:** 0.71.0 · branch `cursor/modo-real-workbench-aafd`  
**DEC:** DEC-123  
**Qué es:** Export JSON server-side de watchlist (`GET /api/watchlist/export`) e import merge/replace (`POST /api/watchlist/import`). Botones Export/Import en Universe. Sin flip LIVE.

**DoD auditor:**
- [ ] GET export → application/json + Content-Disposition
- [ ] POST import mode merge|replace
- [ ] UI `#un-export` / `#un-import`
- [ ] Sin `FASE_79_APPROVED.md`
- [ ] `LIVE_BLOCKED is True`
- [ ] `phases_summary` F19–F79
- [ ] Bump 0.71.0

### Lista A F79

| ID | Artefacto | Path |
|----|-----------|------|
| A1 | Export helpers | `workbench/watchlist.py` |
| A2 | GET/POST watchlist IO | `api.py` + `server.py` |
| A3 | UI Universe | `static/js/panes/universe.js` |
| A4 | DEC-123 | `learning/decisiones.txt` |
| A5 | Version 0.71.0 | `pyproject.toml` |
| A6 | Smoke F79 | `scripts/internal_audit_smoke.py` |
| A7 | Bundle to-phase 79 | `scripts/build_internal_review_bundle.py` |

### Lista B F79 (QA)

```
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Versión código F79: **0.71.0** · LIVE: **BLOQUEADO** · flip: **NO**.

