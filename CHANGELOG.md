# Changelog

Todos los cambios notables de QuantLab se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

---

## [Unreleased]

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
