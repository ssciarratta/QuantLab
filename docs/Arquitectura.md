# QuantLab — Arquitectura del Sistema

**Versión:** 1.1  
**Fase:** 1 — Diseño (Iteración 1.1 — correcciones obligatorias post-revisión)  
**Estado:** Pendiente de segunda revisión  
**Autor:** Cursor (CTO / Arquitecto Principal)

---

## Tabla de contenidos

1. [Arquitectura general](#1-arquitectura-general)
2. [Árbol completo del proyecto](#2-árbol-completo-del-proyecto)
3. [Diagrama de arquitectura](#3-diagrama-de-arquitectura)
4. [Definición de módulos](#4-definición-de-módulos)
5. [Contratos de dominio](#5-contratos-de-dominio)
6. [Interfaces principales](#6-interfaces-principales)
7. [Arquitectura de simulación](#7-arquitectura-de-simulación)
8. [Calidad de datos](#8-calidad-de-datos)
9. [Slippage, fills y granularidad](#9-slippage-fills-y-granularidad)
10. [Flujo de datos](#10-flujo-de-datos)
11. [Decisiones tecnológicas](#11-decisiones-tecnológicas)
12. [Riesgos](#12-riesgos)
13. [Roadmap](#13-roadmap)
14. [Future Improvements](#14-future-improvements)
15. [Autoevaluación crítica](#15-autoevaluación-crítica)

---

## 1. Arquitectura general

### 1.1 Visión

QuantLab es el **sistema central de un laboratorio de investigación cuantitativa**. Su propósito no es ejecutar trades en producción, sino proporcionar la infraestructura para:

- Adquirir, validar y versionar datos de mercado.
- Transformar datos en features reutilizables.
- Descubrir oportunidades (Alpha Scanner).
- Simular estrategias con rigor científico (backtesting bar-based y de microestructura + Monte Carlo).
- Validar resultados con metodología científica (walk-forward, out-of-sample).
- Optimizar parámetros de forma reproducible.
- Generar reportes comparativos y auditables.
- Exportar estrategias validadas hacia un motor de ejecución externo (Hummingbot).

### 1.2 Objetivos

| # | Objetivo | Métrica de éxito futura |
|---|----------|-------------------------|
| O1 | Modularidad | Nueva estrategia sin modificar más de 1 módulo |
| O2 | Reproducibilidad | Determinismo exacto en el mismo entorno controlado; equivalencia numérica con tolerancias documentadas entre entornos; versionado completo del entorno |
| O3 | Escalabilidad | Escalabilidad progresiva hacia 1M+ simulaciones sin modificar los contratos principales del dominio, aceptando cambios de infraestructura y orquestación |
| O4 | Multi-exchange | Nuevo exchange = nuevo conector, sin tocar simulación |
| O5 | Multi-estrategia | 30+ estrategias coexistiendo con interfaces comunes |
| O6 | Multi-activo | 100+ activos en pipeline paralelo |
| O7 | Trazabilidad | Todo experimento tiene ID, config, datos y resultados versionados |
| O8 | Mantenibilidad | Onboarding de nuevo desarrollador en < 1 semana |

### 1.3 Alcance

**Incluido (diseño completo, implementación futura):**

- Pipeline de datos (ingesta → almacenamiento → calidad → features).
- Motor de investigación (Alpha Scanner, registro de experimentos).
- Motor de simulación descompuesto (backtest bar-based, backtest de microestructura, Monte Carlo, optimización).
- Validación científica (train/validation/test, walk-forward).
- Motor de métricas y reportes desacoplados de implementaciones concretas.
- Adaptador de ejecución hacia Hummingbot (exportación, no orquestación live).
- Infraestructura transversal (config, logging, catálogo, manifests).

**Excluido de QuantLab (delegado a sistemas externos):**

- Ejecución directa de órdenes en exchange.
- UI gráfica (fase inicial; reportes estáticos primero).
- Gestión de wallets / custodia.
- Infraestructura cloud (fase inicial local; cloud como extensión).

### 1.4 Principios de diseño

1. **Interface-first con disciplina** — Abstraer solo cuando hay frontera externa real, dos implementaciones plausibles o necesidad demostrada.
2. **Data as first-class citizen** — Los datos tienen esquema, versión, linaje y catálogo.
3. **Experiment-driven** — Toda corrida es un experimento registrado, no un script ad-hoc.
4. **Fail fast, log everything** — Validación temprana; logging estructurado en cada capa.
5. **Immutable snapshots** — Los datos usados en un experimento no cambian retroactivamente.
6. **Separation of concerns** — Investigación ≠ simulación ≠ métricas ≠ reporting ≠ ejecución.
7. **Convention over configuration** — Estructura predecible; config solo para lo que varía.
8. **Progressive complexity** — Empezar simple (local, secuencial), escalar sin reescribir contratos de dominio.
9. **Intenciones, no ejecución** — Strategy produce intenciones; el simulador decide fills, fees y latencia.
10. **Raw inmutable** — `data/raw/` conserva datos originales sin mutación; la normalización produce `data/processed/`.

**Principio registrado (DEC-013):**

> No crear una abstracción sin una frontera externa real, dos implementaciones plausibles o una necesidad demostrada.

### 1.5 Restricciones

- Lenguaje principal: **Python 3.11+**.
- Almacenamiento local inicial; cloud como extensión futura.
- Sin dependencias de un exchange específico en el core.
- Sin acoplamiento directo a Hummingbot en módulos de investigación.
- Sin GUI en fases iniciales.
- Todo código futuro debe tener tests (pytest).
- CI básico desde Fase 2 (instalación limpia, lint, type checking, tests, validación de config).

### 1.6 Supuestos

- Los datos de mercado llegan como series temporales (OHLCV, trades, order book snapshots/deltas).
- Hummingbot permanece como motor de ejecución; QuantLab no lo reemplaza.
- El equipo de investigación opera en entorno local o servidor dedicado con almacenamiento en disco.
- Las estrategias comparten un contrato event-driven (`Strategy`) aunque su lógica interna difiera.
- La fidelidad de simulación requerida depende de la familia de estrategia (bar-based vs microestructura).
- La optimización masiva puede ejecutarse en batch (no requiere latencia sub-milisegundo).
- Los reportes iniciales serán archivos estáticos (HTML/Markdown/Parquet), no dashboards en tiempo real.

---

## 2. Árbol completo del proyecto

```
QuantLab/
│
├── README.md
├── LICENSE
├── CHANGELOG.md
├── LESSONS_LEARNED.md
├── REVIEW_REQUEST.md
├── .gitignore
├── pyproject.toml                     # [Fase 2] Dependencias bloqueadas
│
├── docs/
│   ├── Arquitectura.md
│   ├── Arquitectura_Explicada.txt
│   ├── Diagrama.md
│   ├── protocols/
│   └── adr/
│
├── learning/
│   ├── diario.txt
│   ├── decisiones.txt
│   └── dudas.txt
│
├── config/
│   ├── base/
│   ├── environments/
│   └── schemas/
│
├── src/
│   └── quantlab/
│       ├── core/                      # Contratos, tipos, excepciones, manifests
│       │   ├── types/                 # Instrument, Order, Fill, SimulationResult...
│       │   └── exceptions/
│       │
│       ├── infra/
│       │   ├── config/
│       │   └── logging/
│       │
│       ├── data/
│       │   ├── providers/
│       │   ├── ingestion/
│       │   ├── storage/
│       │   ├── quality/               # Controles de calidad de datos
│       │   └── catalog/
│       │
│       ├── features/
│       │
│       ├── research/
│       │   ├── alpha_scanner/
│       │   ├── experiments/
│       │   ├── validation/            # Scientific Validation (walk-forward, OOS)
│       │   └── strategies/
│       │
│       ├── simulation/
│       │   ├── orchestrator/          # Backtest Orchestrator
│       │   ├── replay/                # Market Replay
│       │   ├── clock/                 # Simulation Clock
│       │   ├── runner/                # Strategy Runner
│       │   ├── execution/             # Execution Simulator + políticas
│       │   ├── ledger/                # Portfolio / Ledger
│       │   ├── recorder/              # Result Recorder
│       │   ├── backtester/            # Facade bar-based (5A) y micro (5B)
│       │   ├── simulator/             # Monte Carlo
│       │   └── optimizer/
│       │
│       ├── metrics/
│       ├── reporting/
│       └── execution/
│
├── tests/
├── experiments/
├── reports/
├── scripts/
└── data/
    ├── raw/                           # Inmutable — datos originales
    ├── processed/                     # Normalizados — no reemplaza raw
    ├── features/
    └── catalog/
```

---

## 3. Diagrama de arquitectura

Ver diagramas completos en [Diagrama.md](Diagrama.md).

### Flujo principal (texto)

```
Data Sources (Exchanges, CSV, APIs)
        ↓
   Ingestion + Data Quality
        ↓
   Raw Storage (inmutable)
        ↓
   Normalización → Processed Storage
        ↓
   Feature Engineering → Feature Store
        ↓
   ┌─────────────┬──────────────────┐
   ↓             ↓                  ↓
Alpha Scanner  Backtest 5A/5B   Experiment Registry
   ↓             ↓
   ↓         Scientific Validation
   ↓             ↓
   ↓         Simulator (Monte Carlo)
   ↓             ↓
   └────→ Optimizer ←────┘
              ↓
        Metrics Engine  ←── SimulationResult (core)
              ↓
       Report Generator ←── ExperimentManifest, MetricsResult (core)
              ↓
     Reports (HTML / Parquet)

   [Aprobación manual]
              ↓
      Execution Engine (export only v1)
              ↓
         Hummingbot → Exchange
```

---

## 4. Definición de módulos

### 4.1 core

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Contratos de dominio, tipos inmutables, manifests y excepciones compartidas |
| **Responsabilidades** | Tipos neutrales (`SimulationResult`, `ExperimentManifest`, `MetricsResult`), contratos conceptuales, jerarquía de errores |
| **Entradas** | Ninguna (módulo raíz) |
| **Salidas** | Contratos importables por todos los módulos |
| **Dependencias** | Ninguna |

### 4.2 infra

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Configuración, logging y utilidades transversales |
| **Dependencias** | `core` |

### 4.3 data

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Adquirir, validar calidad, almacenar y catalogar datos |
| **Responsabilidades** | Ingesta, controles de calidad, normalización a processed, catálogo DuckDB |
| **Regla raw/processed** | Raw inmutable; processed es derivado versionado, nunca reemplaza raw |
| **Dependencias** | `core`, `infra` |

### 4.4 features

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Transformar datos processed en features reutilizables |
| **Dependencias** | `data`, `core` |

### 4.5 research

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Estrategias, experimentos, Alpha Scanner y validación científica |
| **Submódulos** | `strategies/`, `experiments/`, `alpha_scanner/`, `validation/` |
| **Dependencias** | `features`, `data`, `core` |

### 4.6 simulation

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Simular estrategias con rigor estadístico en dos niveles de fidelidad |
| **Salidas** | `SimulationResult` (contrato en core) |
| **Dependencias** | `features`, `data`, `core` |

Ver [§7 Arquitectura de simulación](#7-arquitectura-de-simulación) para descomposición interna.

### 4.7 metrics

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Calcular KPIs de forma consistente |
| **Entradas** | `SimulationResult`, `MetricsResult` inputs (contratos de core) |
| **Salidas** | `MetricsResult` |
| **Dependencias** | **`core` únicamente** — no depende de implementaciones de `simulation` |
| **Regla** | Metrics consume contratos neutrales; nunca importa clases concretas del backtester |

### 4.8 reporting

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Generar reportes auditables y comparativos |
| **Entradas** | `ExperimentManifest`, `SimulationResult`, `MetricsResult` (core) |
| **Dependencias** | **`core`, `metrics`** — no depende de implementaciones de `research` ni `simulation` |
| **Regla** | Reporting renderiza contratos; no accede a estado interno de estrategias |

### 4.9 execution

| Atributo | Descripción |
|----------|-------------|
| **Objetivo** | Exportar estrategias aprobadas hacia motores de ejecución |
| **Alcance v1** | `validate_export`, `build_execution_package`, `export_configuration` |
| **Fuera de alcance v1** | deploy, status, stop, kill switch, orchestration (extensiones futuras) |
| **Dependencias** | `core` |

---

## 5. Contratos de dominio

> Definición **conceptual**. Sin implementaciones. Tipos inmutables en `core/types/`.

### 5.1 Instrument

**Propósito:** Identificar un activo negociable con sus reglas de mercado.

**Campos mínimos:** `instrument_id`, `symbol`, `base_asset`, `quote_asset`, `venue_id`, `tick_size`, `lot_size`, `min_notional`, `status` (active/delisted), `metadata` (historial de cambios de símbolo).

### 5.2 Venue

**Propósito:** Representar un exchange o lugar de ejecución con sus reglas.

**Campos mínimos:** `venue_id`, `name`, `timezone`, `fee_schedule_ref`, `latency_profile_ref`, `constraints` (rate limits, min order size).

### 5.3 MarketEvent

**Propósito:** Evento unificado del bus de simulación.

**Campos mínimos:** `event_id`, `event_type`, `timestamp`, `instrument_id`, `payload` (tipado según subtipo).

**Subtipos:** bar, trade, order_book_snapshot, order_book_delta, timer, order_accepted, order_rejected, partial_fill, full_fill, canceled, expired, balance_update, position_update.

### 5.4 Bar

**Propósito:** OHLCV agregado en intervalo temporal.

**Campos mínimos:** `instrument_id`, `open`, `high`, `low`, `close`, `volume`, `timestamp_open`, `timestamp_close`, `timeframe`.

### 5.5 Trade

**Propósito:** Tick de mercado ejecutado.

**Campos mínimos:** `instrument_id`, `price`, `quantity`, `side` (buy/sell aggressor), `timestamp`, `trade_id`.

### 5.6 OrderBookSnapshot

**Propósito:** Estado completo del libro en un instante.

**Campos mínimos:** `instrument_id`, `timestamp`, `bids[]` (price, qty), `asks[]` (price, qty), `sequence_id`.

### 5.7 OrderBookDelta

**Propósito:** Cambio incremental del libro.

**Campos mínimos:** `instrument_id`, `timestamp`, `sequence_id`, `changes[]` (side, price, qty, action: add/update/delete).

### 5.8 OrderIntent

**Propósito:** Intención de la estrategia — no implica ejecución.

**Campos mínimos:** `intent_id`, `intent_type` (place/cancel/replace/no_action), `instrument_id`, `side`, `quantity`, `price`, `order_type`, `time_in_force`, `replace_target_id` (si replace).

### 5.9 Order

**Propósito:** Orden reconocida por el simulador o venue.

**Campos mínimos:** `order_id`, `client_order_id`, `instrument_id`, `side`, `quantity`, `filled_quantity`, `price`, `status`, `created_at`, `updated_at`.

### 5.10 Fill

**Propósito:** Ejecución parcial o total de una orden.

**Campos mínimos:** `fill_id`, `order_id`, `instrument_id`, `price`, `quantity`, `fee`, `timestamp`, `liquidity` (maker/taker).

### 5.11 Fee

**Propósito:** Costo de transacción desglosado.

**Campos mínimos:** `fee_id`, `fill_id`, `amount`, `currency`, `fee_type` (maker/taker/funding/other).

### 5.12 Position

**Propósito:** Exposición neta en un instrumento.

**Campos mínimos:** `instrument_id`, `quantity`, `avg_entry_price`, `unrealized_pnl`, `realized_pnl`, `updated_at`.

### 5.13 Balance

**Propósito:** Saldo de un activo en el portfolio.

**Campos mínimos:** `asset`, `available`, `locked`, `total`, `updated_at`.

### 5.14 PortfolioState

**Propósito:** Snapshot agregado de posiciones, balances y PnL.

**Campos mínimos:** `timestamp`, `positions[]`, `balances[]`, `total_equity`, `total_realized_pnl`, `total_unrealized_pnl`.

### 5.15 ExecutionReport

**Propósito:** Reporte del ciclo de vida de una orden desde el simulador.

**Campos mínimos:** `order_id`, `status`, `fills[]`, `reject_reason`, `timestamp`.

### 5.16 SimulationClock

**Propósito:** Reloj virtual de la simulación.

**Campos mínimos:** `current_time`, `mode` (event-driven/step), `speed` (realtime/accelerated).

### 5.17 DatasetManifest

**Propósito:** Describir un dataset versionado e inmutable.

**Campos mínimos:** `dataset_id`, `version`, `source`, `instruments[]`, `time_range`, `granularity`, `schema_version`, `checksum`, `row_count`, `storage_path`, `created_at`.

**Versionado de schema:** `schema_version` es obligatorio y sigue la política de
[docs/MANIFEST_VERSIONING.md](MANIFEST_VERSIONING.md) (DEC-036). No confundir con
`version` del dataset ni con la versión de QuantLab.

### 5.18 ExperimentManifest

**Propósito:** Registro completo para reproducibilidad de un experimento.

**Campos mínimos:** `experiment_id`, `dataset_id`, `dataset_version`, `resolved_config`, `seed`, `git_commit`, `python_version`, `dependency_versions_or_hash`, `platform`, `strategy_version`, `execution_model_versions` (fee/slippage/latency/fill), `artifacts_produced[]`, `created_at`, `status`.

### 5.19 SimulationResult

**Propósito:** Contrato neutral de salida de cualquier simulación.

**Campos mínimos:** `experiment_id`, `equity_curve[]`, `fills[]`, `orders[]`, `portfolio_snapshots[]`, `events_log[]`, `metrics_summary` (opcional pre-calculado), `metadata` (modelos usados, duración, seed).

### 5.20 MetricsResult

**Propósito:** Contrato neutral de salida del motor de métricas.

**Campos mínimos:** `experiment_id`, `metrics` (dict nombre→valor), `computed_at`, `metrics_version`, `benchmarks` (opcional).

---

## 6. Interfaces principales

> Definición **conceptual**. Las interfaces marcadas como **Fase N** no se implementan antes de esa fase.
> Fase 2 implementa solo tipos de dominio, manifests y contratos del vertical slice — no las diez interfaces abstractas.

### 6.1 Strategy (rediseñada — event-driven)

**Propósito:** Contrato universal orientado a eventos. Produce **intenciones**, no asume ejecución.

**Modelo conceptual:**

```
Strategy recibe MarketEvent → procesa → retorna OrderIntent[]
```

**Eventos que debe contemplar el contrato:**

| Categoría | Eventos |
|-----------|---------|
| Market data | bar, trade, order_book_snapshot, order_book_delta |
| Timer | timer (heartbeat, rebalance, quote refresh) |
| Order lifecycle | order_accepted, order_rejected, partial_fill, full_fill, canceled, expired |
| Portfolio | balance_update, position_update |

**Intenciones que produce:**

| Intención | Descripción |
|-----------|-------------|
| `place_order` | Nueva orden |
| `cancel_order` | Cancelar orden existente |
| `replace_order` | Cancel-replace |
| `no_action` | Sin cambios |

**Operaciones conceptuales:**

- `on_event(event: MarketEvent, context) → list[OrderIntent]` — handler universal
- `on_bar(bar, context) → list[OrderIntent]` — **adaptador opcional** para estrategias bar-based; no es el contrato universal
- `get_parameters()` / `set_parameters(params)` — para optimización
- `get_state()` / `reset()` — serialización y reinicio

**Regla:** El simulador traduce intenciones en órdenes, aplica FillModel/LatencyModel/FeeModel, y emite eventos de lifecycle de vuelta a Strategy.

**Implementaciones futuras:** PureMarketMaking (5B), SimpleMomentum (5A), InventorySkew, AvellanedaStoikov.

### 6.2 DataProvider — Fase 3

**Operaciones:** `get_bars`, `get_trades`, `get_orderbook_snapshot`, `list_symbols`, `get_metadata`.

### 6.3 Storage — Fase 3

**Operaciones:** `write`, `read`, `list_versions`, `exists`, `delete`.

### 6.4 Backtester — Fase 5A / 5B

**Propósito:** Facade sobre el Backtest Orchestrator (§7).

**Operaciones:** `run(strategy, dataset_manifest, experiment_manifest) → SimulationResult`.

**5A:** datos OHLCV, barras ≥ 1 minuto, políticas baseline.  
**5B:** trades, order book, lifecycle completo, políticas de microestructura.

### 6.5 Simulator — Fase 11 (Monte Carlo)

**Operaciones:** `run(...) → list[SimulationResult]`, `get_distribution()`, `get_confidence_intervals()`.

### 6.6 Optimizer — Fase 12

**Requisito previo:** Scientific Validation aprobada (Fase 9).

**Operaciones:** `optimize(...)`, `get_search_history()`, `get_pareto_front()`, `get_sensitivity()`.

### 6.7 MetricsEngine — Fase 7

**Entrada:** `SimulationResult` (core). **Salida:** `MetricsResult` (core).

**Operaciones:** `calculate(simulation_result, metrics_list) → MetricsResult`, `compare(...)`, `rank(...)`.

### 6.8 AlphaScanner — Fase 13

**Operaciones:** `scan(...)`, `get_opportunities(...)`, `explain(...)`.

### 6.9 ExecutionEngine — Fase 15 (alcance v1)

**Propósito:** Puente QuantLab → Hummingbot. Solo exportación en v1.

**Operaciones v1:**

- `validate_export(experiment_manifest) → ValidationResult`
- `build_execution_package(experiment_manifest) → ExecutionPackage`
- `export_configuration(package, target_path) → ExportResult`

**Extensiones futuras (no v1):** `deploy`, `get_status`, `stop`, kill switch, orchestration multi-bot.

### 6.10 ReportGenerator — Fase 7

**Entrada:** `ExperimentManifest`, `MetricsResult`, `SimulationResult` (core).

**Operaciones:** `generate(...)`, `compare(...)`, `list_templates()`.

---

## 7. Arquitectura de simulación

El Backtester no es un monolito. Se descompone en componentes con responsabilidades claras.

### 7.1 Componentes

| Componente | Responsabilidad | Entradas | Salidas | Depende de |
|------------|-----------------|----------|---------|------------|
| **Backtest Orchestrator** | Coordina la corrida end-to-end | Strategy, DatasetManifest, ExperimentManifest, config | SimulationResult | Todos los subcomponentes |
| **Market Replay** | Reproduce eventos históricos en orden | Dataset (bars/trades/book) | Stream de MarketEvent | DatasetManifest |
| **Simulation Clock** | Avanza el tiempo virtual | Eventos, config de clock | Timestamp actual | — |
| **Strategy Runner** | Invoca Strategy.on_event, recolecta OrderIntent | MarketEvent, Strategy | OrderIntent[] | Strategy |
| **Execution Simulator** | Traduce intenciones en órdenes, aplica políticas | OrderIntent[], MarketEvent, políticas | ExecutionReport, Fill | Fee/Slippage/Latency/FillModel |
| **Portfolio / Ledger** | Contabilidad: posiciones, balances, PnL, fees | Fill[], Fee[] | PortfolioState | — |
| **Result Recorder** | Persiste artefactos de la corrida | Eventos, fills, equity | SimulationResult | ExperimentManifest |

### 7.2 Políticas intercambiables (Execution Simulator)

| Política | Propósito | Fase |
|----------|-----------|------|
| **FeeModel** | Maker/taker fees, descuentos, funding | 5A (simple), 5B (completo) |
| **SlippageModel** | Impacto de precio al ejecutar | 5A (fixed bps baseline), 5B (book-based) |
| **LatencyModel** | Retraso submit→acknowledge→fill | 5B |
| **FillModel** | Condiciones de fill parcial/total | 5B |

Las políticas se registran en `ExperimentManifest.execution_model_versions` para reproducibilidad.

### 7.3 Flujo interno de una corrida

```
Orchestrator
  → Market Replay emite MarketEvent
  → Simulation Clock avanza
  → Strategy Runner → OrderIntent[]
  → Execution Simulator (políticas) → Fill / ExecutionReport
  → Portfolio / Ledger actualiza PortfolioState
  → eventos de lifecycle vuelven a Strategy Runner
  → Result Recorder acumula SimulationResult
```

### 7.4 Dos niveles de backtesting

| Nivel | Fase | Datos | Objetivo |
|-------|------|-------|----------|
| **5A — Bar-based** | 6 | OHLCV ≥ 1 min | Validar arquitectura, contabilidad, fees, métricas, reproducibilidad, golden runs |
| **5B — Microestructura** | 7 | Trades, book snapshots/deltas | Pure MM, partial fills, latency, cancel/replace, inventory, venue constraints |

**Regla:** No declarar validada una estrategia de market making utilizando solamente OHLCV.

---

## 8. Calidad de datos

### 8.1 Principio raw/processed

- **`data/raw/`:** datos originales tal como llegan. **Nunca se mutan.**
- **`data/processed/`:** normalización, deduplicación, alineación temporal. Derivado versionado.
- Un fallo de calidad en processed no destruye raw; se regenera processed desde raw.

### 8.2 Controles conceptuales

| Control | Descripción | Acción ante fallo |
|---------|-------------|-------------------|
| Timestamps monotónicos | Orden temporal estricto por instrumento | Reject o flag en catálogo |
| Duplicados | Mismo event_id/trade_id/bar timestamp | Deduplicar en processed; reportar en raw metadata |
| Gaps | Huecos temporales vs timeframe esperado | Registrar gap; no interpolar en raw |
| Secuencias faltantes | Order book sequence_id discontinuo | Flag; reconstruir solo en processed si es posible |
| Eventos fuera de orden | timestamp < último evento | Reorder en processed; preservar raw |
| Precios/volúmenes imposibles | price ≤ 0, volume < 0 | Reject registro |
| Bid > ask | Spread negativo en snapshot | Reject o flag según severidad |
| Timezone | Todo en UTC internamente | Convertir en processed; documentar TZ original en raw |
| Checksums | Hash por archivo/partición | Validar integridad en catálogo |
| Cobertura | % del rango temporal esperado | Registrar en DatasetManifest |
| Tick size / lot size | Precios y cantidades alineados a reglas del instrumento | Validar contra Instrument metadata |
| Metadata histórica | Cambios de símbolo, delistings, splits | Instrument registry versionado |

### 8.3 Integración en pipeline

1. Ingesta → raw (sin transformación).
2. Quality checks → reporte de calidad.
3. Normalización → processed (solo si quality aceptable o con flags documentados).
4. DatasetManifest registra checksums, cobertura, quality report.

---

## 9. Slippage, fills y granularidad

### 9.1 Reglas por familia de estrategia

| Aspecto | Bar-based (5A) | Microestructura (5B) | Market Making |
|---------|----------------|----------------------|---------------|
| Datos | OHLCV ≥ 1 min | Trades + book | Trades + book obligatorio |
| Slippage default | Fixed bps (baseline aceptable) | Book-based / queue model | **Fixed bps NO es default válido** |
| Fills | Modelo simplificado (bar close/vwap) | FillModel con partial fills | FillModel + inventory |
| Latency | Opcional / fijo | LatencyModel obligatorio | LatencyModel obligatorio |
| Validación MM | **No válida** | **Requerida** | Solo en 5B |

### 9.2 Granularidad temporal

- **OHLCV 1 minuto:** infraestructura, análisis general, estrategias bar-based, golden runs de contabilidad.
- **Tick / book:** estrategias sensibles a ejecución, market making, validación de fills.
- La fidelidad requerida **depende de la familia de estrategia**, no es global.

### 9.3 Fixed bps

- Aceptable **únicamente** como baseline para estrategias bar-based (Fase 5A).
- **No** es default válido para market making ni para Fase 5B.
- Documentar supuestos del modelo en ExperimentManifest.

---

## 10. Flujo de datos

### 10.1 Ingesta (Exchange → Raw)

1. Conector descarga datos vía DataProvider.
2. Validación de esquema mínimo.
3. Escritura en `data/raw/` sin mutación.
4. Catálogo registra DatasetManifest con checksum.

### 10.2 Calidad + Procesamiento (Raw → Processed)

1. Controles de calidad (§8).
2. Normalización: UTC, tipos, deduplicación.
3. Escritura en `data/processed/` con nueva versión.
4. DatasetManifest actualizado.

### 10.3 Features (Processed → Features)

1. Pipelines leen processed.
2. Features versionadas en `data/features/`.

### 10.4 Simulación

1. ExperimentManifest registrado (seed, commit, config, dataset version).
2. Backtest Orchestrator ejecuta según nivel 5A o 5B.
3. SimulationResult persistido.

### 10.5 Métricas y reportes

1. MetricsEngine consume SimulationResult → MetricsResult.
2. ReportGenerator consume ExperimentManifest + MetricsResult + SimulationResult.
3. Reporte en `reports/{experiment_id}/`.

### 10.6 Exportación (v1)

1. Aprobación manual.
2. ExecutionEngine: validate → build package → export config Hummingbot.

---

## 11. Decisiones tecnológicas

(Sin cambios respecto a v1.0: Python 3.11+, Parquet, DuckDB/SQLite, Polars/Pandas, pytest, YAML/TOML, structlog.)

Ver sección 7 de v1.0 para tablas comparativas detalladas.

---

## 12. Riesgos

| # | Riesgo | Impacto | Probabilidad | Mitigación |
|---|--------|---------|--------------|------------|
| R1 | Escalabilidad de simulaciones | Alto | Media | Streaming/chunking; paralelismo; contratos estables |
| R2 | Consumo de memoria | Alto | Alta | Polars lazy; particionado Parquet |
| R3 | Acoplamiento estrategia-datos | Alto | Media | Solo vía Market Replay; prohibir acceso directo a storage |
| R4 | Reproducibilidad rota | Crítico | Baja | ExperimentManifest completo; snapshots inmutables |
| R5 | Latencia de ingesta | Medio | Alta | Retry/backoff; ingesta batch |
| R6 | Versionado de config | Medio | Media | Config en git; snapshot en manifest |
| R7 | Complejidad prematura | Medio | Alta | DEC-013; Fase 2 mínima; interfaces conceptuales hasta su fase |
| R8 | Dependencia Hummingbot | Medio | Media | Adaptador aislado; export-only v1 |
| R9 | Deuda de tests | Alto | Media | CI desde Fase 2; golden runs en 5A |
| R10 | Pérdida de datos | Alto | Baja | Backup; raw inmutable |
| R11 | **Look-ahead bias** | Crítico | Media | Simulation Clock estricto; features solo con datos disponibles al timestamp; tests de leakage |
| R12 | **Survivorship bias** | Alto | Media | Instrument registry con delistings; universo temporal explícito en manifest |
| R13 | **Data leakage** | Crítico | Media | Separación train/val/test; walk-forward; features sin futuro |
| R14 | **Data snooping** | Alto | Media | Scientific Validation obligatoria antes de Optimizer |
| R15 | **Parameter overfitting** | Alto | Alta | Walk-forward; OOS test; control de overfitting en Fase 9 |
| R16 | **Múltiples comparaciones** | Alto | Alta | Corrección estadística; benchmarks; registro de todas las corridas |
| R17 | **Fill model optimista** | Crítico | Alta | 5B obligatorio para MM; sensibilidad de FillModel; FI post-trade analytics |
| R18 | **Market impact ignorado** | Alto | Media | SlippageModel en 5B; documentar supuestos |
| R19 | **Cambios de régimen** | Alto | Media | Walk-forward; métricas por subperíodo |
| R20 | **Delistings / cambios de símbolo** | Medio | Media | Instrument metadata histórica; quality checks |
| R21 | **Errores de contabilidad** | Crítico | Media | Golden runs 5A; invariantes en Ledger; tests de PnL |
| R22 | **Resultados no deterministas** | Alto | Media | Seed fija; documentar paralelismo; tolerancias entre entornos |

---

## 13. Roadmap

> Fases 0–1 completadas (fundación + diseño). Implementación desde Fase 2.

### Fase 2 — Fundación del dominio, manifests y CI

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Tipos fundamentales, manifests, config, logging, CI |
| **Entregables** | Tipos de dominio (§5), DatasetManifest, ExperimentManifest, config, logging, excepciones mínimas, contratos del vertical slice, pyproject.toml con deps bloqueadas, CI (install, lint, mypy, pytest, config validation), tests de infraestructura |
| **No incluye** | Las 10 interfaces abstractas; Simulator, Optimizer, AlphaScanner, ExecutionEngine, ReportGenerator como ABC |
| **Criterio de cierre** | CI verde; manifests serializan/deserializan; config valida; tipos importables |

### Fase 3 — Datos, catálogo y calidad

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Pipeline raw→processed, catálogo, controles de calidad |
| **Entregables** | DataProvider (Mock + CSV), Storage (Parquet), quality checks (§8), catálogo DuckDB |
| **Criterio de cierre** | Ingesta → raw inmutable → quality → processed → catálogo; reproducible |

### Fase 4 — Vertical slice reproducible

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | End-to-end mínimo: dataset → manifest → resultado stub → reporte básico |
| **Entregables** | Pipeline con datos sintéticos, ExperimentManifest completo, SimulationResult stub, reporte mínimo |
| **Criterio de cierre** | Mismo manifest + seed → mismo resultado stub; trazabilidad completa |

### Fase 5 — Features

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Pipelines composables de features |
| **Entregables** | 3+ transformers, pipeline composable, feature store |
| **Criterio de cierre** | Features versionadas sobre datos reales |

### Fase 6 — Backtester bar-based (5A)

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Validar arquitectura de simulación con OHLCV |
| **Entregables** | Componentes §7 con FillModel/FeeModel/SlippageModel baseline, estrategia bar-based simple, golden runs |
| **Criterio de cierre** | Golden runs reproducibles; contabilidad cuadra; metrics básicas; **no validar MM aquí** |

### Fase 7 — Backtester de microestructura (5B)

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Pure MM y estrategias sensibles a ejecución |
| **Entregables** | Market Replay con trades/book, LatencyModel, FillModel completo, cancel/replace, inventory |
| **Criterio de cierre** | MM validada solo con datos de microestructura; partial fills; maker/taker |

### Fase 8 — Métricas y reporting

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | KPIs estandarizados y reportes sobre contratos neutrales |
| **Entregables** | MetricsEngine → MetricsResult, ReportGenerator, template HTML |
| **Criterio de cierre** | Metrics y reporting sin importar simulation/research concretos |

### Fase 9 — Experiment Registry completo

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Lifecycle formal de experimentos |
| **Entregables** | CRUD, estados, vinculación manifest/artefactos |
| **Criterio de cierre** | Experimento registrado → ejecutado → reportado → reproducido |

### Fase 10 — Scientific Validation

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Validación científica antes de optimización |
| **Entregables** | Train/validation/OOS test, walk-forward, prevención look-ahead/leakage, benchmarks, control overfitting, múltiples comparaciones, selección temporal del universo |
| **Criterio de cierre** | Ninguna optimización sin pipeline de validación aprobado |
| **Requisito** | Obligatorio antes de Fase 12 (Optimizer) |

### Fase 11 — Monte Carlo

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Simulaciones estocásticas masivas |
| **Entregables** | Simulator, N escenarios, intervalos de confianza |
| **Criterio de cierre** | 10K escenarios reproducibles (seed fija) |

### Fase 12 — Optimizer

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Búsqueda de parámetros con validación previa |
| **Dependencias** | Fase 10 aprobada |
| **Entregables** | Grid/random search, historial, sensibilidad |
| **Criterio de cierre** | Optimización con OOS validation; Pareto multi-objetivo |

### Fase 13 — Alpha Scanner

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Selección automática de oportunidades |
| **Entregables** | Scanner, ranking, explicabilidad |
| **Criterio de cierre** | Scan 10+ activos; universo temporal explícito |

### Fase 14 — Estrategias avanzadas

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Inventory Skew, Adaptive MM, Avellaneda & Stoikov |
| **Dependencias** | Fase 7 (5B) |
| **Criterio de cierre** | Cada estrategia validada en 5B |

### Fase 15 — Multi-exchange

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Múltiples exchanges |
| **Entregables** | Provider adicional, normalización cross-exchange |
| **Criterio de cierre** | 2+ exchanges en catálogo unificado |

### Fase 16 — Hummingbot (export v1)

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Exportar estrategias aprobadas |
| **Entregables** | ExecutionEngine v1 (validate, build, export) |
| **Criterio de cierre** | Config exportada y validada; sin deploy live obligatorio |

### Fase 17 — Escalabilidad distribuida

| Atributo | Detalle |
|----------|---------|
| **Objetivo** | Volumen real de investigación |
| **Entregables** | Paralelismo distribuido, monitoring, backup |
| **Criterio de cierre** | 100K+ simulaciones; contratos de dominio sin cambios |

---

## 14. Future Improvements

> Walk-forward movido a Fase 10 (Scientific Validation). No implementar sin autorización.

| # | Mejora | Módulo | Prioridad |
|---|--------|--------|-----------|
| FI-01 | Event sourcing para experimentos | research/experiments | Media |
| FI-02 | Feature store online | features | Baja |
| FI-03 | Hot paths Rust/PyO3 | simulation | Alta (si profiling lo justifica) |
| FI-04 | Orchestrador distribuido | simulation | Alta (Fase 17) |
| FI-05 | Dashboard web | reporting | Media |
| FI-06 | AutoML feature selection | research | Baja |
| FI-07 | Data lake S3/MinIO | data | Media |
| FI-08 | Schema registry | data/catalog | Baja |
| FI-09 | Paper trading interno | execution | Media |
| FI-10 | Post-trade analytics loop | data + metrics | Alta |
| FI-11 | ML meta-strategy | research | Baja |
| FI-12 | Property-based testing (Hypothesis) | tests | Media |
| FI-13 | Config hot-reload | infra | Baja |

---

## 15. Autoevaluación crítica

### Fortalezas

1. Strategy event-driven con intenciones — apta para market making.
2. Contratos de dominio explícitos — metrics/reporting desacoplados.
3. Backtester descompuesto — políticas intercambiables.
4. Dos niveles de fidelidad (5A/5B) — evita falsa validación de MM.
5. Scientific Validation antes de Optimizer.
6. Fase 2 realista — no congela interfaces prematuras.

### Debilidades residuales

| # | Debilidad | Severidad | Acción |
|---|-----------|-----------|--------|
| W1 | FillModel/LatencyModel aún conceptuales | Media | Detallar en diseño de Fase 7 |
| W2 | Instrument registry no tiene fase propia | Baja | Incluir en Fase 3 |
| W3 | Tolerancias numéricas cross-env no cuantificadas | Media | Definir en Fase 6 con golden runs |

### Confianza post-corrección: **8/10**

---

*Documento v1.1 — Iteración post-revisión técnica PROMPT 001.1. Pendiente segunda revisión.*
