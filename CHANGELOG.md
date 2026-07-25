# Changelog

Todos los cambios notables de QuantLab se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

---

## [Unreleased]

### Added
- Fase 5 M2: FeeModel (`ZeroFee`, `Proportional`, `MakerTaker`)
- Fase 5 M3: `ArtifactsEngine` + bundle manifest
- Regla `auto-next-module.mdc`
- DEC-049, DEC-050

### Changed
- Versión **0.5.0**
- `BarSimulationEngine` integra fee_model
- `PortfolioTracker` acepta fee explícito

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
