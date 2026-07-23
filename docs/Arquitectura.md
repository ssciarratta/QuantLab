# QuantLab — Arquitectura del Sistema

**Versión:** 1.0  
**Fase:** 1 — Diseño  
**Estado:** Pendiente de revisión  
**Autor:** Cursor (CTO / Arquitecto Principal)

---

## Tabla de contenidos

1. [Arquitectura general](#1-arquitectura-general)
2. [Árbol completo del proyecto](#2-árbol-completo-del-proyecto)
3. [Diagrama de arquitectura](#3-diagrama-de-arquitectura)
4. [Definición de módulos](#4-definición-de-módulos)
5. [Interfaces principales](#5-interfaces-principales)
6. [Flujo de datos](#6-flujo-de-datos)
7. [Decisiones tecnológicas](#7-decisiones-tecnológicas)
8. [Riesgos](#8-riesgos)
9. [Roadmap](#9-roadmap)
10. [Future Improvements](#10-future-improvements)
11. [Autoevaluación crítica](#11-autoevaluación-crítica)

---

## 1. Arquitectura general

### 1.1 Visión

QuantLab es el **sistema central de un laboratorio de investigación cuantitativa**. Su propósito no es ejecutar trades en producción, sino proporcionar la infraestructura para:

- Adquirir, validar y versionar datos de mercado.
- Transformar datos en features reutilizables.
- Descubrir oportunidades (Alpha Scanner).
- Simular estrategias con rigor científico (backtesting + Monte Carlo).
- Optimizar parámetros de forma reproducible.
- Generar reportes comparativos y auditables.
- Exportar estrategias validadas hacia un motor de ejecución externo (Hummingbot).

### 1.2 Objetivos

| # | Objetivo | Métrica de éxito futura |
|---|----------|-------------------------|
| O1 | Modularidad | Nueva estrategia sin modificar más de 1 módulo |
| O2 | Reproducibilidad | Mismo experimento → mismos resultados (bit a bit en métricas clave) |
| O3 | Escalabilidad | 1M+ simulaciones sin rediseño arquitectónico |
| O4 | Multi-exchange | Nuevo exchange = nuevo conector, sin tocar simulación |
| O5 | Multi-estrategia | 30+ estrategias coexistiendo con interfaces comunes |
| O6 | Multi-activo | 100+ activos en pipeline paralelo |
| O7 | Trazabilidad | Todo experimento tiene ID, config, datos y resultados versionados |
| O8 | Mantenibilidad | Onboarding de nuevo desarrollador en < 1 semana |

### 1.3 Alcance

**Incluido (diseño completo, implementación futura):**

- Pipeline de datos (ingesta → almacenamiento → features).
- Motor de investigación (Alpha Scanner, registro de experimentos).
- Motor de simulación (backtest, Monte Carlo, optimización).
- Motor de métricas y reportes.
- Adaptador de ejecución hacia Hummingbot.
- Infraestructura transversal (config, logging, catálogo).

**Excluido de QuantLab (delegado a sistemas externos):**

- Ejecución directa de órdenes en exchange.
- UI gráfica (fase inicial; reportes estáticos primero).
- Gestión de wallets / custodia.
- Infraestructura cloud (fase inicial local; cloud como extensión).

### 1.4 Principios de diseño

1. **Interface-first** — Todo módulo expone una interfaz; la implementación es intercambiable.
2. **Data as first-class citizen** — Los datos tienen esquema, versión, linaje y catálogo.
3. **Experiment-driven** — Toda corrida es un experimento registrado, no un script ad-hoc.
4. **Fail fast, log everything** — Validación temprana; logging estructurado en cada capa.
5. **Immutable snapshots** — Los datos usados en un experimento no cambian retroactivamente.
6. **Separation of concerns** — Investigación ≠ ejecución ≠ reporting.
7. **Convention over configuration** — Estructura predecible; config solo para lo que varía.
8. **Progressive complexity** — Empezar simple (local, secuencial), escalar sin reescribir interfaces.

### 1.5 Restricciones

- Lenguaje principal: **Python 3.11+**.
- Almacenamiento local inicial; cloud como extensión futura.
- Sin dependencias de un exchange específico en el core.
- Sin acoplamiento directo a Hummingbot en módulos de investigación.
- Sin GUI en fases iniciales.
- Todo código futuro debe tener tests (pytest).

### 1.6 Supuestos

- Los datos de mercado llegan como series temporales (OHLCV, trades, order book snapshots).
- Hummingbot permanece como motor de ejecución; QuantLab no lo reemplaza.
- El equipo de investigación opera en entorno local o servidor dedicado con almacenamiento en disco.
- Las estrategias comparten un contrato común (`Strategy`) aunque su lógica interna difiera.
- La optimización masiva puede ejecutarse en batch (no requiere latencia sub-milisegundo).
- Los reportes iniciales serán archivos estáticos (HTML/Markdown/Parquet), no dashboards en tiempo real.

---

## 2. Árbol completo del proyecto

```
QuantLab/
│
├── README.md                          # Entrada al proyecto
├── LICENSE                            # Licencia MIT
├── CHANGELOG.md                       # Historial de cambios por fase
├── LESSONS_LEARNED.md                 # Lecciones al cierre de cada fase
├── REVIEW_REQUEST.md                  # Solicitud formal de revisión
├── .gitignore                         # Exclusiones (data, reports, secrets)
├── pyproject.toml                     # [Fase 2] Dependencias y metadata Python
│
├── docs/
│   ├── Arquitectura.md                # Este documento
│   ├── Arquitectura_Explicada.txt     # Versión en lenguaje claro
│   ├── Diagrama.md                    # Diagramas Mermaid
│   ├── protocols/                     # [Fase 2+] Protocolos de desarrollo
│   └── adr/                           # [Fase 2+] Architecture Decision Records
│
├── learning/
│   ├── diario.txt                     # Bitácora diaria del proyecto
│   ├── decisiones.txt                 # Registro de decisiones técnicas
│   └── dudas.txt                      # Dudas abiertas pendientes de resolver
│
├── config/
│   ├── base/                          # Configuración base compartida
│   │   ├── logging.yaml               # Config de logging
│   │   └── defaults.yaml              # Defaults globales
│   ├── environments/                  # Overrides por entorno
│   │   ├── dev.yaml
│   │   ├── research.yaml
│   │   └── production.yaml            # Solo para exportación a ejecución
│   └── schemas/                       # Esquemas de validación de config
│       ├── experiment.schema.yaml
│       └── dataset.schema.yaml
│
├── src/
│   └── quantlab/
│       ├── __init__.py
│       │
│       ├── core/                      # Núcleo: interfaces, tipos, excepciones
│       │   ├── interfaces/            # Contratos abstractos de cada módulo
│       │   ├── types/                 # Tipos de dominio (Bar, Order, Signal...)
│       │   └── exceptions/            # Jerarquía de errores del sistema
│       │
│       ├── infra/                     # Infraestructura transversal
│       │   ├── config/                # Carga y validación de configuración
│       │   ├── logging/               # Setup de logging estructurado
│       │   └── utils/                 # Utilidades genéricas (paths, hashing)
│       │
│       ├── data/                      # Capa de datos
│       │   ├── providers/             # Implementaciones de DataProvider
│       │   ├── ingestion/             # Pipelines de ingesta
│       │   ├── storage/               # Implementaciones de Storage
│       │   └── catalog/               # Catálogo y linaje de datasets
│       │
│       ├── features/                  # Feature engineering
│       │   ├── transformers/          # Transformaciones individuales
│       │   └── pipelines/             # Pipelines composables de features
│       │
│       ├── research/                  # Capa de investigación
│       │   ├── alpha_scanner/         # Alpha Scanner
│       │   ├── experiments/           # Registro y lifecycle de experimentos
│       │   └── strategies/            # Implementaciones de Strategy
│       │       ├── market_making/     # Pure MM, Inventory Skew, Adaptive...
│       │       └── avellaneda_stoikov/ # [Futuro]
│       │
│       ├── simulation/                # Capa de simulación
│       │   ├── backtester/            # Motor de backtesting
│       │   ├── simulator/             # Monte Carlo y escenarios
│       │   └── optimizer/             # Optimización de parámetros
│       │
│       ├── metrics/                   # Motor de métricas
│       │   ├── calculators/           # Sharpe, drawdown, fill rate...
│       │   └── aggregators/           # Agregación multi-estrategia / multi-activo
│       │
│       ├── reporting/                 # Generación de reportes
│       │   ├── templates/             # Plantillas HTML/Markdown
│       │   └── exporters/             # Export a HTML, PDF, Parquet
│       │
│       └── execution/                 # Capa de ejecución (adaptadores)
│           ├── engine/                # ExecutionEngine
│           └── adapters/              # Hummingbot adapter, paper trading...
│
├── tests/
│   ├── unit/                          # Tests unitarios por módulo
│   ├── integration/                   # Tests de integración entre capas
│   ├── fixtures/                      # Datos sintéticos para tests
│   └── conftest.py                    # Fixtures compartidas pytest
│
├── experiments/
│   ├── registry/                      # Registros JSON/YAML de experimentos ejecutados
│   └── definitions/                   # Definiciones de experimentos reutilizables
│
├── reports/                           # Reportes generados (gitignored)
│   └── .gitkeep
│
├── scripts/
│   ├── ingest/                        # Scripts operativos de ingesta
│   ├── run_experiment/                # CLI para lanzar experimentos
│   └── maintenance/                   # Limpieza, migración, health checks
│
└── data/                              # Datos locales (gitignored)
    ├── raw/                           # Datos crudos tal como llegan
    ├── processed/                     # Datos normalizados
    ├── features/                      # Features calculadas
    └── catalog/                       # Índice DuckDB de datasets
```

### Justificación de carpetas

| Carpeta | Propósito | ¿Por qué existe? |
|---------|-----------|---------------------|
| `docs/` | Documentación viva del sistema | Un laboratorio cuantitativo sin documentación no es reproducible |
| `docs/adr/` | Architecture Decision Records | Registra el "por qué" de cada decisión importante |
| `learning/` | Memoria del equipo | Decisiones, dudas y bitácora separadas del código |
| `config/` | Configuración versionada | Separar config de código permite reproducir experimentos |
| `src/quantlab/core/` | Interfaces y tipos | Punto único de contratos; evita acoplamiento |
| `src/quantlab/infra/` | Transversal | Config y logging no pertenecen a ningún dominio |
| `src/quantlab/data/` | Datos | Primera capa del pipeline; independiente de estrategias |
| `src/quantlab/features/` | Features | Separar feature engineering de estrategias permite reutilización |
| `src/quantlab/research/` | Investigación | Alpha Scanner y experimentos viven aquí, no en simulación |
| `src/quantlab/simulation/` | Simulación | Backtest, Monte Carlo y optimización comparten datos, no lógica |
| `src/quantlab/metrics/` | Métricas | Un solo lugar para definir KPIs; evita duplicación |
| `src/quantlab/reporting/` | Reportes | Desacoplado de simulación; mismo reporte para distintos motores |
| `src/quantlab/execution/` | Ejecución | Frontera clara con el mundo live; adaptadores intercambiables |
| `tests/` | Calidad | Cada módulo con tests; fixtures con datos sintéticos |
| `experiments/` | Registro científico | Los experimentos son artefactos del laboratorio, no logs temporales |
| `reports/` | Salida | Generados, no versionados; pueden ser grandes |
| `scripts/` | Operaciones | CLIs y tareas batch fuera del paquete importable |
| `data/` | Almacenamiento local | Datos pesados fuera de git; estructura predecible |

---

## 3. Diagrama de arquitectura

Ver diagramas completos en [Diagrama.md](Diagrama.md).

### Flujo principal (texto)

```
Data Sources (Exchanges, CSV, APIs)
        ↓
   Ingestion Engine
        ↓
   Validación + Normalización
        ↓
   Raw Storage (Parquet)
        ↓
   Procesamiento temporal
        ↓
   Processed Storage (Parquet)
        ↓
   Feature Engineering
        ↓
   Feature Store (Parquet)
        ↓
   ┌─────────────┬──────────────┐
   ↓             ↓              ↓
Alpha Scanner  Backtester    Experiment Registry
   ↓             ↓
   ↓         Simulator (Monte Carlo)
   ↓             ↓
   └────→ Optimizer ←────┘
              ↓
        Metrics Engine
              ↓
       Report Generator
              ↓
     Reports (HTML / Parquet)
              
   [Aprobación manual]
              ↓
      Execution Engine
              ↓
         Hummingbot
              ↓
          Exchange
```

---

## 4. Definición de módulos

### 4.1 core

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Definir contratos, tipos de dominio y excepciones compartidas |
| **Responsabilidades** | Interfaces abstractas, tipos inmutables, jerarquía de errores |
| **Entradas** | Ninguna (módulo raíz) |
| **Salidas** | Contratos importables por todos los módulos |
| **Dependencias** | Ninguna |
| **Extensiones futuras** | Nuevos tipos de dominio (options, futures), nuevas interfaces |

### 4.2 infra

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Proveer configuración, logging y utilidades transversales |
| **Responsabilidades** | Cargar config por entorno, setup de logging estructurado, helpers de paths/hashing |
| **Entradas** | Archivos YAML/TOML de `config/` |
| **Salidas** | Objetos de config validados, logger configurado |
| **Dependencias** | `core` |
| **Extensiones futuras** | Telemetría, tracing distribuido, secrets manager |

### 4.3 data

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Adquirir, validar, almacenar y catalogar datos de mercado |
| **Responsabilidades** | Conectores de ingesta, normalización, storage Parquet, catálogo DuckDB |
| **Entradas** | Feeds de exchanges, archivos CSV/Parquet, APIs |
| **Salidas** | Datasets versionados en `data/processed/`, entradas en catálogo |
| **Dependencias** | `core`, `infra` |
| **Extensiones futuras** | Nuevos exchanges (nuevo provider), streaming en tiempo real, data lake S3 |

**Submódulos:**

- `providers/` — Implementaciones de `DataProvider` (Binance, CSV local, etc.)
- `ingestion/` — Pipelines batch de descarga y carga
- `storage/` — Implementaciones de `Storage` (Parquet local, futuro S3)
- `catalog/` — Metadatos, linaje, versiones de datasets

### 4.4 features

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Transformar datos procesados en features reutilizables |
| **Responsabilidades** | Pipelines composables de transformaciones (volatilidad, spread, volumen...) |
| **Entradas** | Datasets procesados |
| **Salidas** | Feature sets en `data/features/` |
| **Dependencias** | `data`, `core` |
| **Extensiones futuras** | Feature store online, auto-feature discovery, ML features |

### 4.5 research

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Descubrir oportunidades y gestionar el ciclo de vida de experimentos |
| **Responsabilidades** | Alpha Scanner, registro de experimentos, implementaciones de estrategias |
| **Entradas** | Features, config de experimento, definiciones de estrategia |
| **Salidas** | Rankings de oportunidades, experimentos registrados, señales |
| **Dependencias** | `features`, `data`, `core` |
| **Extensiones futuras** | AutoML para selección de features, meta-learning entre estrategias |

**Submódulos clave:**

- `alpha_scanner/` — Evalúa activos/mercados y rankea oportunidades
- `experiments/` — CRUD de experimentos, estados (draft → running → completed → approved)
- `strategies/` — Implementaciones concretas de `Strategy`

### 4.6 simulation

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Simular estrategias con rigor estadístico |
| **Responsabilidades** | Backtesting event-driven, Monte Carlo, optimización de parámetros |
| **Entradas** | Strategy + dataset + config de simulación |
| **Salidas** | Resultados de simulación (trades, equity curve, distribuciones) |
| **Dependencias** | `features`, `data`, `core` |
| **Extensiones futuras** | Simulación distribuida, GPU acceleration, walk-forward automático |

**Submódulos:**

- `backtester/` — Simulación histórica event-driven con modelado de latencia/slippage
- `simulator/` — Monte Carlo: perturbación de parámetros, escenarios, bootstrap
- `optimizer/` — Grid search, bayesian optimization, genetic algorithms

### 4.7 metrics

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Calcular y agregar KPIs de forma consistente |
| **Responsabilidades** | Sharpe, Sortino, max drawdown, fill rate, inventory risk, PnL, etc. |
| **Entradas** | Resultados de simulación (trades, equity) |
| **Salidas** | Métricas estructuradas (dict / Parquet) |
| **Dependencias** | `core`, `simulation` (solo tipos de salida) |
| **Extensiones futuras** | Métricas custom por estrategia, benchmarks, risk parity |

### 4.8 reporting

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Generar reportes auditables y comparativos |
| **Responsabilidades** | Templates, export HTML/Markdown/Parquet, comparación multi-experimento |
| **Entradas** | Métricas, resultados, metadata de experimento |
| **Salidas** | Archivos en `reports/` |
| **Dependencias** | `metrics`, `research` |
| **Extensiones futuras** | Dashboard web, alertas, reportes programados |

### 4.9 execution

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Exportar estrategias aprobadas hacia motores de ejecución |
| **Responsabilidades** | Traducir config QuantLab → config Hummingbot, validar pre-flight |
| **Entradas** | Experimento aprobado + config de estrategia |
| **Salidas** | Archivo de config para Hummingbot, confirmación de despliegue |
| **Dependencias** | `core`, `research` |
| **Extensiones futuras** | Paper trading interno, multi-bot orchestration, kill switch |

---

## 5. Interfaces principales

> Definición **conceptual**. Sin código. Cada interfaz será un contrato abstracto en `core/interfaces/`.

### 5.1 DataProvider

**Propósito:** Abstraer la fuente de datos de mercado.

**Operaciones conceptuales:**
- `get_bars(symbol, timeframe, start, end)` → serie temporal OHLCV
- `get_trades(symbol, start, end)` → tick data
- `get_orderbook_snapshot(symbol, timestamp)` → snapshot de libro
- `list_symbols()` → universo de activos disponibles
- `get_metadata()` → info del provider (exchange, latencia, límites)

**Implementaciones futuras:** BinanceProvider, CSVProvider, ParquetProvider, MockProvider (tests).

### 5.2 Storage

**Propósito:** Abstraer la persistencia de datasets.

**Operaciones conceptuales:**
- `write(dataset_id, data, schema_version)` → persiste con versionado
- `read(dataset_id, version)` → recupera snapshot inmutable
- `list_versions(dataset_id)` → historial de versiones
- `exists(dataset_id, version)` → verificación
- `delete(dataset_id, version)` → limpieza (con confirmación)

**Implementaciones futuras:** ParquetStorage (local), S3Storage (cloud).

### 5.3 Strategy

**Propósito:** Contrato universal para toda estrategia de trading.

**Operaciones conceptuales:**
- `on_bar(bar, context)` → procesa nueva barra; retorna señales/órdenes
- `on_fill(fill, context)` → callback de ejecución
- `get_parameters()` → parámetros actuales (para optimización)
- `set_parameters(params)` → inyección de parámetros
- `get_state()` → estado interno serializable (inventario, posición)
- `reset()` → reinicio para nueva simulación

**Implementaciones futuras:** PureMarketMaking, InventorySkew, AdaptiveMM, AvellanedaStoikov.

### 5.4 Backtester

**Propósito:** Simular una estrategia sobre datos históricos.

**Operaciones conceptuales:**
- `run(strategy, dataset, config)` → ejecuta backtest completo
- `get_results()` → trades, equity curve, eventos
- `get_config()` → config usada (para reproducibilidad)

**Parámetros de config:** slippage model, fee schedule, latency model, initial capital.

### 5.5 Simulator

**Propósito:** Ejecutar simulaciones estocásticas (Monte Carlo).

**Operaciones conceptuales:**
- `run(strategy, dataset, config, n_scenarios, seed)` → N escenarios
- `get_distribution()` → distribución de métricas clave
- `get_scenario(id)` → detalle de un escenario individual
- `get_confidence_intervals(levels)` → intervalos de confianza

### 5.6 Optimizer

**Propósito:** Encontrar parámetros óptimos de una estrategia.

**Operaciones conceptuales:**
- `optimize(strategy, dataset, param_space, objective, method)` → mejor config
- `get_search_history()` → todas las combinaciones evaluadas
- `get_pareto_front()` → frente de Pareto (multi-objetivo)
- `get_sensitivity()` → análisis de sensibilidad por parámetro

**Métodos futuros:** grid, random, bayesian, genetic.

### 5.7 MetricsEngine

**Propósito:** Calcular KPIs de forma estandarizada.

**Operaciones conceptuales:**
- `calculate(results, metrics_list)` → dict de métricas
- `compare(results_a, results_b)` → delta entre dos corridas
- `rank(results_list, objective)` → ranking de múltiples corridas
- `register_custom_metric(name, fn)` → extensibilidad

**Métricas estándar:** total_pnl, sharpe_ratio, sortino_ratio, max_drawdown, win_rate, fill_rate, avg_spread_captured, inventory_turnover.

### 5.8 AlphaScanner

**Propósito:** Evaluar y rankear oportunidades de mercado automáticamente.

**Operaciones conceptuales:**
- `scan(universe, features, criteria)` → ranking de activos/mercados
- `get_opportunities(top_n)` → top N oportunidades con score
- `explain(symbol)` → desglose de por qué un activo rankea alto/bajo
- `update_criteria(criteria)` → modificar criterios de selección

### 5.9 ExecutionEngine

**Propósito:** Puente entre QuantLab y motores de ejecución live.

**Operaciones conceptuales:**
- `validate(strategy_config)` → pre-flight checks
- `export(experiment_id, target)` → genera config para Hummingbot
- `deploy(config)` → envía config al motor (futuro)
- `get_status()` → estado del despliegue
- `stop()` → detener ejecución

### 5.10 ReportGenerator

**Propósito:** Producir reportes a partir de resultados de experimentos.

**Operaciones conceptuales:**
- `generate(experiment_id, template, format)` → reporte renderizado
- `compare(experiment_ids, template)` → reporte comparativo
- `list_templates()` → plantillas disponibles
- `register_template(name, template)` → extensibilidad

---

## 6. Flujo de datos

### 6.1 Ingesta (Exchange → Raw Storage)

1. Un **conector de ingesta** (script o pipeline) solicita datos al exchange vía `DataProvider`.
2. Los datos crudos se validan contra un **esquema** definido en `config/schemas/`.
3. Si la validación pasa, se escriben en `data/raw/{exchange}/{symbol}/{timeframe}/` como Parquet particionado.
4. El **catálogo** (DuckDB) registra: dataset_id, versión, timestamp, hash, filas, rango temporal.

### 6.2 Procesamiento (Raw → Processed)

1. Un pipeline de procesamiento lee datos raw del catálogo.
2. Normaliza: timezones UTC, tipos consistentes, deduplicación, fill de gaps.
3. Escribe en `data/processed/` con el mismo esquema de partición.
4. Actualiza catálogo con nueva versión processed.

### 6.3 Feature Engineering (Processed → Features)

1. Pipelines de features leen datos processed.
2. Aplican transformaciones composables (volatilidad rolling, spread medio, volumen relativo...).
3. Escriben feature sets en `data/features/`.
4. Cada feature set tiene metadata: inputs usados, parámetros, versión.

### 6.4 Investigación (Features → Alpha Scanner)

1. Alpha Scanner recibe universo de activos + feature sets.
2. Aplica criterios configurables (spread, volumen, volatilidad, correlación...).
3. Produce ranking de oportunidades con scores y explicaciones.
4. Registra resultado como experimento en `experiments/registry/`.

### 6.5 Simulación (Features + Strategy → Results)

1. Se selecciona estrategia, activo, rango temporal y parámetros.
2. Se registra experimento con ID único, seed, versiones de datos.
3. **Backtester** ejecuta simulación event-driven sobre datos históricos.
4. Opcionalmente, **Simulator** ejecuta N escenarios Monte Carlo perturbando parámetros.
5. Opcionalmente, **Optimizer** busca mejores parámetros en el espacio definido.
6. Resultados (trades, equity, distribuciones) se almacenan referenciados al experiment_id.

### 6.6 Métricas y reportes (Results → Reports)

1. **MetricsEngine** calcula KPIs estandarizados sobre resultados.
2. **ReportGenerator** renderiza reporte usando template + métricas + metadata.
3. Reporte se escribe en `reports/{experiment_id}/`.
4. Reporte incluye: config usada, versiones de datos, seed, métricas, gráficos (futuro).

### 6.7 Ejecución (Aprobación → Hummingbot → Exchange)

1. Investigador aprueba experimento manualmente.
2. **ExecutionEngine** valida config pre-flight.
3. Exporta config compatible con Hummingbot.
4. Hummingbot ejecuta en exchange (fuera de QuantLab).
5. QuantLab puede recibir fills de vuelta para análisis post-trade (futuro).

---

## 7. Decisiones tecnológicas

### 7.1 Python 3.11+

| Ventajas | Desventajas |
|----------|-------------|
| Ecosistema cuantitativo maduro (numpy, polars, scipy) | GIL limita paralelismo CPU puro |
| Tipado gradual con type hints | Performance inferior a Rust/C++ para hot paths |
| Productividad alta para investigación | Gestión de dependencias puede ser frágil |
| Integración natural con Jupyter para exploración | |
| `tomllib` built-in desde 3.11 | |

**Decisión:** Python como lenguaje principal. Hot paths futuros (simulador inner loop) pueden migrarse a Rust via PyO3 si profiling lo justifica.

### 7.2 Parquet

| Ventajas | Desventajas |
|----------|-------------|
| Columnar: lectura selectiva eficiente | No ideal para datos pequeños (< 1000 filas) |
| Compresión excelente (snappy, zstd) | Schema evolution requiere disciplina |
| Compatible con Polars, DuckDB, Pandas | Escritura random-access limitada |
| Particionamiento nativo por directorio | |
| Estándar de facto en data engineering | |

**Decisión:** Parquet como formato universal de almacenamiento de series temporales.

### 7.3 DuckDB (primario) + SQLite (fallback)

| Criterio | DuckDB | SQLite |
|----------|--------|--------|
| Analytics sobre Parquet | Nativo, cero-copy | Requiere import |
| Agregaciones grandes | Optimizado columnar | Row-based, más lento |
| Catálogo de metadata | Excelente | Suficiente para pocos datasets |
| Concurrencia escritura | Single-writer | Single-writer |
| Dependencias | Zero external deps | Built-in Python |
| Portabilidad | Archivo único .duckdb | Archivo único .db |

**Decisión:** DuckDB como motor analítico y catálogo (`data/catalog/`). SQLite solo como fallback si DuckDB presenta problemas en algún entorno.

### 7.4 Polars (primario) + Pandas (compatibilidad)

| Criterio | Polars | Pandas |
|----------|--------|--------|
| Performance | 5-30x más rápido en agregaciones | Baseline |
| Memoria | Lazy evaluation, streaming | Eager por defecto |
| API | Expresiva, tipo Rust | Estándar de la industria |
| Ecosistema | Creciendo, compatible con Arrow | Enorme, toda librería cuant lo soporta |
| Curva de aprendizaje | Distinta a Pandas | Familiar para todos |

**Decisión:** Polars como motor principal de transformación. Pandas solo en fronteras donde una librería externa lo requiera (ej. ciertos indicadores técnicos).

### 7.5 Pytest

| Ventajas | Desventajas |
|----------|-------------|
| Estándar de facto en Python | Fixtures complejas pueden ser difíciles de seguir |
| Fixtures, parametrización, markers | No es framework de benchmarking |
| Integración con CI (futuro) | |
| Plugins: pytest-cov, pytest-xdist (paralelo) | |

**Decisión:** pytest para toda la pirámide de tests (unit + integration).

### 7.6 Configuración (YAML + TOML)

| Formato | Uso |
|---------|-----|
| `pyproject.toml` | Metadata del proyecto, dependencias, tools |
| `config/**/*.yaml` | Configuración de runtime (entornos, experimentos, datasets) |
| `experiments/definitions/*.yaml` | Definiciones de experimentos |

**Ventajas:** Legible, versionable, diff-friendly.  
**Desventajas:** Sin tipado nativo (se compensa con schemas de validación en `config/schemas/`).

### 7.7 Logging (structlog)

| Ventajas | Desventajas |
|----------|-------------|
| Logs estructurados (JSON) facilitan búsqueda | Overhead mínimo vs print |
| Context binding (experiment_id, module) | Dependencia adicional |
| Compatible con stdlib logging | |
| Preparado para agregadores futuros (ELK, Datadog) | |

**Decisión:** structlog sobre stdlib logging, configurado via `config/base/logging.yaml`.

---

## 8. Riesgos

| # | Riesgo | Impacto | Probabilidad | Mitigación |
|---|--------|---------|--------------|------------|
| R1 | **Escalabilidad de simulaciones** — 1M+ escenarios agotan RAM/tiempo | Alto | Media | Diseño con streaming/chunking desde el inicio; paralelismo via multiprocessing; interfaces preparadas para workers distribuidos |
| R2 | **Consumo de memoria** — datasets grandes cargados completos en RAM | Alto | Alta | Polars lazy evaluation; lectura particionada de Parquet; procesamiento por ventanas temporales |
| R3 | **Acoplamiento estrategia-datos** — estrategias acceden a storage directamente | Alto | Media | Prohibir acceso directo; solo via interfaces; inyección de datos en backtester |
| R4 | **Reproducibilidad rota** — datos mutados retroactivamente | Crítico | Baja | Snapshots inmutables; versionado en catálogo; hash de datasets en experimento |
| R5 | **Latencia de ingesta** — APIs de exchange con rate limits | Medio | Alta | Cola de ingesta con retry/backoff; cache local; ingesta batch nocturna |
| R6 | **Versionado de config** — configs cambian sin registro | Medio | Media | Config versionada en git; schemas de validación; config snapshot en experimento |
| R7 | **Complejidad prematura** — over-engineering en fases tempranas | Medio | Alta | Progressive complexity; implementar lo mínimo viable por fase; Future Improvements para lo no urgente |
| R8 | **Dependencia de Hummingbot** — cambios en su API rompen adaptador | Medio | Media | Adaptador aislado en `execution/adapters/`; tests de contrato; version pinning |
| R9 | **Deuda de tests** — módulos sin cobertura | Alto | Media | Test obligatorio por módulo antes de cerrar fase; CI futuro |
| R10 | **Pérdida de datos** — disco local sin backup | Alto | Baja | Documentar estrategia de backup; cloud como extensión; catálogo regenerable desde Parquet |

---

## 9. Roadmap

### Fase 2 — Core + Infraestructura

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Establecer contratos, config, logging y tipos base |
| **Dependencias** | Fase 1 aprobada |
| **Entregables** | `core/` (interfaces + tipos), `infra/` (config + logging), tests unitarios, `pyproject.toml` |
| **Criterio de cierre** | Todas las interfaces definidas (abstractas); config carga y valida; logging funciona; tests pasan |

### Fase 3 — Capa de datos

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Pipeline de ingesta, storage Parquet, catálogo DuckDB |
| **Dependencias** | Fase 2 |
| **Entregables** | `DataProvider` (MockProvider + CSVProvider), `Storage` (ParquetStorage), catálogo, scripts de ingesta |
| **Criterio de cierre** | Ingestar CSV → Parquet → catálogo → leer de vuelta; reproducible; testeado |

### Fase 4 — Feature Engineering

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Pipelines composables de features |
| **Dependencias** | Fase 3 |
| **Entregables** | 3+ transformers (volatilidad, spread, volumen), pipeline composable, feature store |
| **Criterio de cierre** | Pipeline ejecuta sobre datos reales; features versionadas; tests con datos sintéticos |

### Fase 5 — Backtester

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Motor de backtesting event-driven con una estrategia simple |
| **Dependencias** | Fase 4, interfaz `Strategy` |
| **Entregables** | Backtester funcional, PureMarketMaking como estrategia de referencia, modelos de slippage/fees |
| **Criterio de cierre** | Backtest reproducible sobre 1 activo; métricas básicas calculadas; testeado |

### Fase 6 — Metrics + Reporting

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | KPIs estandarizados y reportes automáticos |
| **Dependencias** | Fase 5 |
| **Entregables** | MetricsEngine, ReportGenerator, template HTML básico |
| **Criterio de cierre** | Reporte generado automáticamente post-backtest; comparación entre 2 experimentos |

### Fase 7 — Experiment Registry

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Ciclo de vida formal de experimentos |
| **Dependencias** | Fase 6 |
| **Entregables** | CRUD experimentos, estados, vinculación config/datos/resultados |
| **Criterio de cierre** | Experimento registrado → ejecutado → reportado → reproducido con mismo ID |

### Fase 8 — Simulator (Monte Carlo)

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Simulaciones estocásticas masivas |
| **Dependencias** | Fase 5 |
| **Entregables** | Simulator con N escenarios, distribuciones, intervalos de confianza |
| **Criterio de cierre** | 10K escenarios reproducibles (seed fija); resultados en Parquet; paralelismo local |

### Fase 9 — Optimizer

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Búsqueda automática de parámetros |
| **Dependencias** | Fase 8 |
| **Entregables** | Grid search + random search; historial de búsqueda; sensibilidad |
| **Criterio de cierre** | Optimización sobre 3+ parámetros; Pareto front en multi-objetivo; reproducible |

### Fase 10 — Alpha Scanner

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Selección automática de oportunidades |
| **Dependencias** | Fase 4, Fase 6 |
| **Entregables** | Scanner con criterios configurables, ranking, explicabilidad |
| **Criterio de cierre** | Scan sobre 10+ activos; ranking reproducible; integrado con experiment registry |

### Fase 11 — Estrategias avanzadas

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Inventory Skew, Adaptive MM, Avellaneda & Stoikov |
| **Dependencias** | Fase 5 |
| **Entregables** | 3 estrategias implementadas con tests y backtests de referencia |
| **Criterio de cierre** | Cada estrategia pasa backtest de referencia; comparables via MetricsEngine |

### Fase 12 — Multi-exchange + DataProvider extensible

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Soporte para múltiples exchanges |
| **Dependencias** | Fase 3 |
| **Entregables** | BinanceProvider (o similar), factory de providers, normalización cross-exchange |
| **Criterio de cierre** | Datos de 2+ exchanges ingeridos y normalizados; catálogo unificado |

### Fase 13 — Execution Engine + Hummingbot

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Exportar estrategias aprobadas a Hummingbot |
| **Dependencias** | Fase 7, Fase 11 |
| **Entregables** | ExecutionEngine, HummingbotAdapter, pre-flight validation |
| **Criterio de cierre** | Config exportada y validada; despliegue documentado; sin ejecución live obligatoria |

### Fase 14 — Escalabilidad y producción

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Preparar para volumen real de investigación |
| **Dependencias** | Fases 8-13 |
| **Entregables** | Paralelismo distribuido, CI/CD, monitoring, backup strategy |
| **Criterio de cierre** | 100K+ simulaciones en tiempo razonable; CI verde; documentación operativa |

---

## 10. Future Improvements

> Registradas para referencia. **No implementar sin autorización.**

| # | Mejora | Módulo afectado | Beneficio | Prioridad |
|---|--------|------------------|-----------|-----------|
| FI-01 | Event sourcing para experimentos | research/experiments | Auditoría completa de cambios de estado | Media |
| FI-02 | Feature store online (Redis/SQLite) | features | Features en tiempo real para scanner live | Baja |
| FI-03 | Hot paths en Rust via PyO3 | simulation | 10-100x speedup en inner loop de Monte Carlo | Alta (cuando profiling lo justifique) |
| FI-04 | Orchestrador distribuido (Celery/Ray) | simulation | Millones de simulaciones en cluster | Alta (Fase 14) |
| FI-05 | Dashboard web (FastAPI + frontend) | reporting | Visualización interactiva de experimentos | Media |
| FI-06 | AutoML para feature selection | research/alpha_scanner | Descubrimiento automático de features predictivas | Baja |
| FI-07 | Walk-forward analysis automático | simulation/backtester | Validación out-of-sample sistemática | Alta |
| FI-08 | Data lake en S3/MinIO | data/storage | Escalabilidad de almacenamiento beyond local | Media |
| FI-09 | Schema registry (Confluent-style) | data/catalog | Evolución controlada de esquemas de datos | Baja |
| FI-10 | Paper trading interno | execution | Validación pre-Hummingbot sin riesgo | Media |
| FI-11 | Post-trade analytics loop | data + metrics | Fills de Hummingbot → análisis de slippage real vs simulado | Alta |
| FI-12 | ML pipeline para meta-strategy | research | Ensemble de estrategias basado en régimen de mercado | Baja |
| FI-13 | ADR automatizado en cada PR | docs/adr | Trazabilidad de decisiones arquitectónicas | Media |
| FI-14 | Property-based testing (Hypothesis) | tests | Validación de invariantes en simulador | Media |
| FI-15 | Config hot-reload | infra/config | Cambiar parámetros sin reiniciar pipeline | Baja |

---

## 11. Autoevaluación crítica

### Fortalezas del diseño

1. **Separación clara de capas** — Datos, features, investigación, simulación, ejecución y reporting son independientes.
2. **Interface-first** — Permite reemplazar cualquier implementación sin efecto cascada.
3. **Reproducibilidad by design** — Snapshots inmutables, versionado, seeds, registro de experimentos.
4. **Escalabilidad progresiva** — Empieza local/simple; interfaces preparadas para distribución.
5. **Roadmap incremental** — 14 fases pequeñas con criterios de cierre claros.

### Debilidades identificadas

| # | Debilidad | Severidad | Acción recomendada |
|---|-----------|-----------|---------------------|
| W1 | **Complejidad inicial alta** — 9 módulos + 10 interfaces pueden intimidar en Fase 2 | Media | Implementar solo interfaces necesarias por fase; no crear módulos vacíos |
| W2 | **Sin estrategia de testing de simulador** — validar correctness del backtester es difícil | Alta | Definir en Fase 5 "golden runs" con resultados conocidos; FI-14 (Hypothesis) |
| W3 | **Catálogo DuckDB como single point** — corrupción del .duckdb pierde metadata | Media | Catálogo regenerable desde Parquet; backup periódico |
| W4 | **Sin definición de latencia model** — critical para MM strategies | Alta | Definir en Fase 5 antes de implementar backtester; documentar supuestos |
| W5 | **Alpha Scanner sin criterios concretos aún** — riesgo de scope creep | Media | Definir criterios mínimos en Fase 10; no antes |
| W6 | **Dependencia de Polars** — si Polars cambia API major, impacto alto | Baja | Abstraer operaciones comunes en `features/`; no usar Polars directo en estrategias |
| W7 | **Sin plan de migración de datos** — cambio de schema puede invalidar datasets | Media | Schema versioning en Parquet metadata; script de migración en `scripts/maintenance/` |

### Preguntas abiertas (ver `learning/dudas.txt`)

- ¿DuckDB o SQLite para catálogo? (Recomendación: DuckDB, con fallback documentado)
- ¿Qué modelo de slippage usar como default? (Depende de estrategias; definir en Fase 5)
- ¿Hummingbot v1 o v2 como target de integración? (Definir en Fase 13)
- ¿Necesitamos order book replay o solo OHLCV para fase inicial? (Recomendación: OHLCV primero)

---

*Documento generado en Fase 1. Pendiente de revisión técnica.*
