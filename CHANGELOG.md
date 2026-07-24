# Changelog

Todos los cambios notables de QuantLab se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

---

## [Unreleased]

---

## [0.2.0] — 2026-07-23

### Fase 2 — Core + Infraestructura (Post-Auditoría v1.1)

#### Added
- `pyproject.toml` con dependencias y configuración de herramientas
- `uv.lock` — lockfile reproducible (DEC-018)
- `src/quantlab/core/types/json_types.py` — Tipos JSON inmutables: JsonScalar, JsonValue, JsonArray, JsonObject (DEC-015)
- `src/quantlab/core/types/market.py` — Instrument, Bar, BookLevel, Trade, Fill, Order con invariantes validadas
- `src/quantlab/core/types/trading.py` — OrderIntent con validación por tipo (DEC-016), MarketEvent, StrategyContext, Balance, TimeRange, SimulationResult, MetricsResult
- `src/quantlab/core/types/experiment.py` — ExperimentManifest con campos mínimos de reproducibilidad
- `src/quantlab/core/interfaces/strategy.py` — Strategy Protocol con on_event() (DEC-013)
- `src/quantlab/core/exceptions/` — Jerarquía de excepciones: QuantLabError, ConfigurationError, ValidationError, DataError, SimulationError, StrategyError
- `src/quantlab/infra/config/` — Configuración con Pydantic, deep merge, validación estricta (DEC-019)
- `src/quantlab/infra/logging/` — Setup de structlog (consola y JSON)
- `src/quantlab/infra/utils/` — Hashing determinista, git commit, project root
- `src/quantlab/cli.py` — DummyStrategy y vertical slice CLI
- `tests/` — 157 tests de comportamiento (invariantes, inmutabilidad, timezone, protocol, config)
- `.github/workflows/ci.yml` — CI completa: install, ruff, mypy, pytest, coverage, vertical slice, gitleaks
- `.gitleaks.toml` — Configuración de escaneo de secretos (DEC-017)
- `config/base/defaults.yaml` — Configuración base
- `config/environments/` — Overrides por entorno (dev, research, production)
- `PROJECT_STATUS.md` — Estado del proyecto
- `scripts/generate_review_package.sh` — Generador del Review Package
- 7 nuevas decisiones técnicas (DEC-013 a DEC-019)

#### Changed
- `REVIEW_REQUEST.md` — Matriz de corrección con 35 hallazgos
- `LESSONS_LEARNED.md` — Lecciones de auditoría
- `README.md` — Actualizado con estado Fase 2
- `learning/decisiones.txt` — DEC-013 a DEC-019 agregadas

#### Security
- Integrado escaneo automático de secretos (Gitleaks)
- CI bloquea si detecta tokens, passwords, claves privadas
- No se encontraron secretos en el repositorio
- `.gitignore` protege .env y *.secret

#### Removed
- Dependencia de `requirements.txt` generado desde entorno global
- `on_bar()` eliminado del protocolo Strategy

---

## [0.1.0] — 2026-07-23

### Fase 1 — Diseño de arquitectura

#### Added
- Arquitectura completa del sistema (`docs/Arquitectura.md`)
- Diagramas de arquitectura en Mermaid (`docs/Diagrama.md`)
- Explicación en lenguaje claro (`docs/Arquitectura_Explicada.txt`)
- Definición de 9 módulos con responsabilidades, entradas, salidas y dependencias
- Definición conceptual de 10 interfaces (DataProvider, Storage, Strategy, Backtester, Simulator, Optimizer, MetricsEngine, AlphaScanner, ExecutionEngine, ReportGenerator)
- Flujo de datos completo (exchange → reportes)
- Decisiones tecnológicas justificadas (Python, Parquet, DuckDB, Polars, pytest, structlog, YAML)
- Identificación de 10 riesgos técnicos con mitigaciones
- Roadmap de implementación en 14 fases
- 15 Future Improvements registradas
- Autoevaluación crítica del diseño
- `LESSONS_LEARNED.md` de Fase 1
- `REVIEW_REQUEST.md` para revisión técnica
- Registro de 12 decisiones técnicas (`learning/decisiones.txt`)
- Registro de 8 dudas abiertas (`learning/dudas.txt`)
- Bitácora del proyecto (`learning/diario.txt`)
- README actualizado con visión, principios y estado del proyecto

#### Changed
- README.md actualizado de "Fase 0" a "Fase 1 — En revisión"

---

## [0.0.1] — 2026-07-23

### Fase 0 — Fundación

#### Added
- Estructura inicial de carpetas (docs, learning, src, tests, experiments, reports, config, scripts, data)
- README.md inicial
- LICENSE (MIT)
- .gitignore (Python, data/, reports/, secrets)
- Repositorio GitHub: https://github.com/ssciarratta/QuantLab
