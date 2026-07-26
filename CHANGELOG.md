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
