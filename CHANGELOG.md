# Changelog

Todos los cambios notables de QuantLab se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

---

## [Unreleased]

### Added
- TD-05: `FixedLatencyModel.min_delay` wall-clock con `bar_times` en `BarSimulationEngine`
- TD-03 research: federación de paper ledger (`node_id`, `reconcile_indexes`, `merge_from`)
- CI Actions versionado: `.github/workflows/ci.yml` (espejo `docs/ci/ci.yml.example`)

### Changed
- `.gitignore`: deja de excluir el workflow de CI
- `sync_phase_github.sh`: `SKIP_WORKFLOWS` default `0` (escape hatch `=1`)

---

## [0.21.0] — 2026-07-26

### Fase 29 — Report Viewer + Metrics History

#### Added
- `workbench/reports.py` — persist MetricsResult/summary (+ HTML ReportGenerator) en session `reports/`
- API `GET /api/lab/reports`, `GET /api/lab/reports/{id}` (POST implícito en backtest)
- Panel UI Reports: lista + preview HTML|JSON
- Tests `test_reports_f29.py` · DEC-073
- Docs: `FASE_29_REPORTS.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); report_id fail-closed (charset / sandbox)

---

## [0.20.0] — 2026-07-26

### Fase 28 — Workbench Layout Persistence + Journal Viewer

#### Added
- `workbench/layout.py` — save/load `layout.json` por sesión (geometría MDI)
- API `GET`/`PUT` `/api/layout`
- `wm.js` debounce save en move/resize + restore al boot
- Panel Journal (`panes/journal.js`): tabla fills + export CSV client-side
- Tests `test_layout_f28.py` · DEC-072
- Docs: `FASE_28_LAYOUT_JOURNAL.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); layout fail-closed (ids/rangos)

---

## [0.19.0] — 2026-07-26

### Fase 27 — Strategy Catalog (workbench)

#### Added
- Catálogo compartido `workbench/strategy_catalog.py` (dummy, buy_once, momentum, inventory_mm, avellaneda_stoikov)
- Wire `InventoryMMStrategy` + `AvellanedaStoikovStrategy` en paper session + lab backtest
- `GET /api/lab/strategies` + `strategy_catalog` en capabilities
- UI selectores + params básicos (Sesión Paper / Backtest)
- Adapter bar-based para MM en lab (`BarSyntheticBookAdapter`)
- Tests smoke por `strategy_id` · DEC-071
- Docs: `FASE_27_STRATEGY_CATALOG.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin place_order venue

---

## [0.18.0] — 2026-07-26

### Fase 26 — Paper Session Runner

#### Added
- `PaperSessionRunner` / `PaperSessionConfig` (`workbench/paper_session.py`)
- API `/api/paper/session/{start,stop,step,status}`
- UI panel «Sesión Paper» (Inicio → Sesión Paper)
- Background opcional `interval_ms` (daemon cancelable)
- Tests `test_paper_session_runner.py`

#### Security
- `LIVE_BLOCKED is True` (sin flip); nunca place_order venue
- Audit INTERNAL: constructor fail-closed solo `PaperBroker` (H1); DEC-070
- Docs: `AUTO_AUDIT_2026-07-26_F26` · `INTERNAL_AUDIT_F26` · noche F19–F26
- `FASE_26_APPROVED.md` **no** emitido (reserva Meta-Auditor externo)

---

## [0.17.0] — 2026-07-26

### Fase 25 — Ops Desk (1-click + hardening)

#### Added
- `scripts/launch_workbench.sh` + `packaging/quantlab-workbench.desktop` + `docs/ops/WORKBENCH_1CLICK.md`
- CLI `--allow-non-loopback` / `--slippage-bps`; `GET /api/risk`; panel Riesgo
- PaperBroker `slippage_bps` adverso (buy/sell worse)
- `validate_experiment_id` charset `^[A-Za-z0-9_-]+$`
- Tests non-loopback, experiment_id, paper slippage; smoke F23/F24/F25

#### Security
- Host no-loopback abort exit 2 sin flag; warning si se permite
- `LIVE_BLOCKED is True` (sin flip)

#### Docs / audit (post-impl)
- INTERNAL APROBADO_INTERNO F25 + arco F23–F25 + noche F19–F25
- DEC-069; tests API risk + allow-non-loopback warning; smoke 11 checks

---

## [0.16.0] — 2026-07-26

### Fase 24 — Venue plugins + MD read-only multiplataforma

#### Added
- Entry points `quantlab.brokers` (`brokers/plugins.py`); `get_default_registry` carga plugins
- A3 `md_source` fake|env (`QUANTLAB_A3_MD_READONLY=1` + creds; fallback fake)
- Builtins `generic_csv` / `generic_rest` (MD-only skeletons)
- Workbench: connect `md_source`; health/session `md_provider` / `plugin_venues`; UI Market provider
- Docs: `docs/ops/BROKER_PLUGINS.md`; DEC-067/068

#### Security
- submit/cancel en A3 + generics → `assert_live_routing_blocked`
- `LIVE_BLOCKED is True` (sin flip)

---

## [0.15.0] — 2026-07-26

### Fase 23 — Paper Book + Session durable + Risk paper

#### Added
- `PaperBook`: posiciones, cash, avg ponderado, equity MTM; `to_dict`/`from_dict`
- `PaperBroker` actualiza book en PLACE; `get_positions`/`get_account` desde book
- `WorkbenchSession` durable bajo `data/runtime/workbench/<id>/`
- `PaperRiskLimits` fail-closed en paper submit (max qty/notional/symbols)
- API: `GET /api/broker/positions`, `GET /api/paper/book`, `GET /api/session`
- UI panel Posiciones + banner `session_id` + equity en blotter
- CLI: `--session-id`, `--session-root`, `--initial-cash`

#### Security
- Short rechazado por defecto (`allow_short=False`)
- `LIVE_BLOCKED is True` (sin flip)

---

## [0.14.0] — 2026-07-26

### Fase 22 — Chat IA safe-by-default (APROBADO_INTERNO)

#### Added
- `workbench/chat/`: ToolRegistry allowlist, FakeProvider, OptionalEnvProvider, ChatAuditLog, ChatOrchestrator
- API `POST /api/chat` + `GET /api/chat/tools`; panel Chat IA + banner safe-mode
- Tests `tests/unit/workbench/test_chat_*.py` (17)
- Smoke `scripts/internal_audit_smoke.py` (LIVE + imports workbench/brokers/chat)
- Auditoría INTERNAL F22 + cierre arco F19–F22

#### Security
- Illegal tools rechazados; chat no puede `set_live` / `place_order` / `submit_order`
- `LIVE_BLOCKED is True`; FakeProvider default CI; `QUANTLAB_LLM_*=DISABLED` en `.env.example`

---

## [0.2.0] — 2026-07-23

### Fase 2 — Fundación del dominio

#### Added
- Paquete `quantlab` con `core/`, `infra/`, `research/strategies/`, `vertical_slice/`
- 20 tipos de dominio inmutables (dataclasses frozen + StrEnum)
- Contrato `Strategy` event-driven (Protocol) + `StrategyContext`
- `DatasetManifest`, `ExperimentManifest`, `SimulationResult`, `MetricsResult`
- Jerarquía de excepciones (`QuantLabError`, `ConfigError`, `ManifestError`, ...)
- Infra: carga YAML, validación Pydantic, structlog, utils reproducibilidad
- `DummyStrategy` + vertical slice end-to-end (`quantlab-vertical-slice`)
- Config: `config/base/`, `config/environments/`
- CI GitHub Actions: ruff, mypy, pytest (≥80% cov), smoke tests
- Review Package v1.0 / v1.1 (obsoletos; reemplazados por v1.2/v1.3)

---

## [0.1.1] — 2026-07-23

### Fase 1 — Iteración 1.1 (correcciones obligatorias PROMPT 001.1)

#### Changed
- `docs/Arquitectura.md` v1.1 y documentos asociados

---

## [0.1.0] — 2026-07-23

### Fase 1 — Diseño de arquitectura

#### Added
- Arquitectura, diagramas, roadmap, decisiones DEC-001..026
