# QuantLab — Diagramas de Arquitectura

> Fase 1 — Iteración 1.1. Solo diseño. Sin implementación.

---

## 1. Vista general del sistema

```mermaid
flowchart TB
    subgraph External["Fuentes externas"]
        EX1[Exchange A]
        EX2[Exchange B]
        EXN[Exchange N]
        ALT[Fuentes alternativas<br/>CSV, APIs, archivos]
    end

    subgraph Ingestion["Capa de ingesta + calidad"]
        ING[Ingestion Engine]
        DQ[Data Quality Checks]
        CAT[Catálogo de datasets]
    end

    subgraph Storage["Capa de almacenamiento"]
        RAW[(Raw — inmutable)]
        PROC[(Processed — Parquet)]
        FEAT[(Features — Parquet)]
        META[(Metadata — DuckDB)]
    end

    subgraph Research["Capa de investigación"]
        FE[Feature Engineering]
        AS[Alpha Scanner]
        EXP[Experiment Registry]
        SV[Scientific Validation]
    end

    subgraph Simulation["Capa de simulación"]
        BT5A[Backtester 5A bar-based]
        BT5B[Backtester 5B microestructura]
        SIM[Simulator Monte Carlo]
        OPT[Optimizer]
    end

    subgraph CoreContracts["Contratos neutrales — core"]
        SR[SimulationResult]
        EM[ExperimentManifest]
        MR[MetricsResult]
    end

    subgraph Output["Capa de salida"]
        MET[Metrics Engine]
        REP[Report Generator]
        RPT[Reports]
    end

    subgraph Execution["Capa de ejecución v1"]
        EE[Execution Engine<br/>export only]
        HB[Hummingbot]
    end

    EX1 & EX2 & EXN & ALT --> ING
    ING --> RAW
    RAW --> DQ --> PROC --> FEAT
    ING --> CAT --> META
    FEAT --> FE --> AS
    FEAT --> BT5A & BT5B
    AS --> EXP
    BT5A & BT5B --> SR
    SIM --> SR
    OPT --> SR
    SR --> MET --> MR
    EM & MR & SR --> REP --> RPT
    AS --> SV
    SV --> OPT
    BT5A --> SIM
    EXP --> EM
    AS -.->|estrategia aprobada| EE --> HB --> EX1
```

---

## 2. Flujo de datos principal

```mermaid
flowchart LR
    A[Exchange / Fuente] --> B[Conector de ingesta]
    B --> C[Raw inmutable]
    C --> D[Quality + normalización]
    D --> E[Feature Store]
    E --> F{Destino}
    F --> G[Alpha Scanner]
    F --> H[Backtest 5A / 5B]
    H --> I[Scientific Validation]
    I --> J[Simulador Monte Carlo]
    J --> K[Optimizador]
    G & K --> L[Metrics Engine]
    L --> M[Report Generator]
    M --> N[Reportes HTML/Parquet]
    G -.-> O[Execution Engine export → Hummingbot]
```

---

## 3. Dependencias entre módulos

```mermaid
flowchart TD
    CORE[core — tipos, manifests, contratos]
    INFRA[infra — config, logging]
    DATA[data — providers, storage, quality, catalog]
    FEAT[features — engineering]
    RES[research — strategies, experiments, validation]
    SIM[simulation — orchestrator, replay, execution...]
    METR[metrics — KPIs]
    REPT[reporting — reportes]
    EXEC[execution — export Hummingbot]

    INFRA --> CORE
    DATA --> CORE
    DATA --> INFRA
    FEAT --> DATA
    FEAT --> CORE
    RES --> FEAT
    RES --> DATA
    RES --> CORE
    SIM --> FEAT
    SIM --> DATA
    SIM --> CORE
    METR --> CORE
    REPT --> CORE
    REPT --> METR
    EXEC --> CORE
```

**Reglas de dependencia (v1.1):**

- `metrics` consume `SimulationResult` y produce `MetricsResult` desde `core`. **No depende de `simulation`.**
- `reporting` consume `ExperimentManifest`, `SimulationResult`, `MetricsResult` desde `core`. **No depende de `research`.**
- Ningún módulo importa implementaciones concretas de otro módulo del mismo nivel.

---

## 4. Arquitectura interna del Backtester

```mermaid
flowchart TB
    ORCH[Backtest Orchestrator]
    REPLAY[Market Replay]
    CLOCK[Simulation Clock]
    RUNNER[Strategy Runner]
    EXEC[Execution Simulator]
    LEDGER[Portfolio / Ledger]
    REC[Result Recorder]

    subgraph Policies["Políticas intercambiables"]
        FEE[FeeModel]
        SLIP[SlippageModel]
        LAT[LatencyModel]
        FILL[FillModel]
    end

    ORCH --> REPLAY
    REPLAY --> CLOCK
    CLOCK --> RUNNER
    RUNNER -->|OrderIntent| EXEC
    EXEC --> Policies
    EXEC -->|Fill| LEDGER
    EXEC -->|ExecutionReport| RUNNER
    LEDGER -->|PortfolioState| RUNNER
    ORCH --> REC
    REC --> SR[SimulationResult]
```

---

## 5. Strategy event-driven

```mermaid
flowchart LR
    subgraph Input["Eventos entrantes"]
        MD[Market data<br/>bar, trade, book]
        TM[Timer]
        OL[Order lifecycle<br/>accepted, fill, cancel...]
        PF[Portfolio<br/>balance, position]
    end

    STRAT[Strategy.on_event]
    OUT[OrderIntent]

    subgraph Intents["Intenciones"]
        PL[place_order]
        CA[cancel_order]
        RE[replace_order]
        NA[no_action]
    end

    MD & TM & OL & PF --> STRAT
    STRAT --> OUT
    OUT --> PL & CA & RE & NA
    PL & CA & RE --> EXEC[Execution Simulator]
```

**Nota:** `on_bar` es adaptador opcional para estrategias bar-based; el contrato universal es `on_event`.

---

## 6. Ciclo de vida de un experimento

```mermaid
sequenceDiagram
    participant R as Researcher
    participant EM as ExperimentManifest
    participant D as Data Layer
    participant O as Backtest Orchestrator
    participant M as Metrics Engine
    participant Rep as Report Generator

    R->>EM: Registra experimento (seed, commit, config)
    EM->>D: Solicita DatasetManifest versionado
    D-->>EM: Dataset snapshot
    EM->>O: Ejecuta backtest 5A o 5B
    O-->>EM: SimulationResult
    EM->>M: Calcula métricas
    M-->>Rep: MetricsResult
    Rep-->>R: Reporte reproducible
    R->>EM: Cierra (aprobado / rechazado)
```

---

## 7. Separación investigación vs ejecución

```mermaid
flowchart LR
    subgraph QuantLab["QuantLab (investigación)"]
        direction TB
        Q1[Datos]
        Q2[Estrategias event-driven]
        Q3[Simulaciones 5A/5B]
        Q4[Scientific Validation]
        Q5[Reportes]
    end

    subgraph Boundary["Frontera de aprobación"]
        APPR[Aprobación manual]
    end

    subgraph Runtime["Runtime v1 — export only"]
        direction TB
        R1[Execution Engine<br/>validate / build / export]
        R2[Hummingbot]
        R3[Exchange live]
    end

    Q5 --> APPR
    APPR -->|execution package| R1
    R1 --> R2 --> R3
```

QuantLab **nunca** envía órdenes directamente. v1 solo exporta configuración validada.

---

## 8. Scientific Validation (antes de Optimizer)

```mermaid
flowchart TB
    DATA[Dataset completo]
    DATA --> TRAIN[Train set]
    DATA --> VAL[Validation set]
    DATA --> OOS[Out-of-sample test]
    TRAIN --> WF[Walk-forward windows]
    VAL --> WF
    WF --> BENCH[Benchmarks]
    OOS --> BENCH
    BENCH --> GATE{¿Aprobado?}
    GATE -->|Sí| OPT[Optimizer]
    GATE -->|No| REJECT[Rechazar / revisar estrategia]
```

---

## 9. Escalabilidad (visión futura — Fase 17)

```mermaid
flowchart TB
    ORCH[Orchestrator de simulaciones]
    W1[Worker 1]
    W2[Worker 2]
    WN[Worker N]
    QUEUE[Cola de tareas]
    STORE[(SimulationResult — Parquet)]

    ORCH --> QUEUE
    QUEUE --> W1 & W2 & WN
    W1 & W2 & WN --> STORE
    STORE --> MET[Metrics Engine]
```

Contratos de dominio sin cambios; solo infraestructura y orquestación evolucionan.
