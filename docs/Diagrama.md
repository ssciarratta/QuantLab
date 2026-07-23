# QuantLab — Diagramas de Arquitectura

> Fase 1 — Solo diseño. Sin implementación.

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

    subgraph Ingestion["Capa de ingesta"]
        ING[Ingestion Engine]
        VAL[Validador de esquema]
        CAT[Catálogo de datasets]
    end

    subgraph Storage["Capa de almacenamiento"]
        RAW[(Raw — Parquet)]
        PROC[(Processed — Parquet)]
        FEAT[(Features — Parquet)]
        META[(Metadata — DuckDB)]
    end

    subgraph Research["Capa de investigación"]
        FE[Feature Engineering]
        AS[Alpha Scanner]
        EXP[Experiment Registry]
    end

    subgraph Simulation["Capa de simulación"]
        BT[Backtester]
        SIM[Simulator Monte Carlo]
        OPT[Optimizer]
        MET[Metrics Engine]
    end

    subgraph Output["Capa de salida"]
        REP[Report Generator]
        RPT[Reports / Dashboards futuro]
    end

    subgraph Execution["Capa de ejecución (futuro)"]
        EE[Execution Engine]
        HB[Hummingbot]
    end

    EX1 & EX2 & EXN & ALT --> ING
    ING --> VAL --> RAW
    RAW --> PROC --> FEAT
    ING --> CAT --> META
    FEAT --> FE --> AS
    FEAT --> BT
    AS --> EXP
    BT --> MET
    SIM --> MET
    OPT --> MET
    MET --> REP --> RPT
    AS --> OPT
    BT --> SIM
    EXP --> REP
    AS -.->|estrategia aprobada| EE --> HB --> EX1
```

---

## 2. Flujo de datos principal

```mermaid
flowchart LR
    A[Exchange / Fuente] --> B[Conector de ingesta]
    B --> C[Validación + normalización]
    C --> D[Raw Storage]
    D --> E[Procesamiento temporal]
    E --> F[Feature Store]
    F --> G{Destino}
    G --> H[Alpha Scanner]
    G --> I[Backtester]
    H --> J[Ranking de oportunidades]
    I --> K[Simulador Monte Carlo]
    K --> L[Optimizador]
    J & L --> M[Metrics Engine]
    M --> N[Report Generator]
    N --> O[Reportes HTML/PDF/Parquet]
    J -.-> P[Execution Engine → Hummingbot]
```

---

## 3. Dependencias entre módulos

```mermaid
flowchart TD
    CORE[core — interfaces, tipos, excepciones]
    INFRA[infra — config, logging, utils]
    DATA[data — providers, storage, catalog]
    FEAT[features — engineering]
    RES[research — alpha scanner, experiments]
    SIM[simulation — backtest, simulator, optimizer]
    METR[metrics — métricas y KPIs]
    REPT[reporting — generador de reportes]
    EXEC[execution — adaptadores Hummingbot]

    INFRA --> CORE
    DATA --> CORE
    DATA --> INFRA
    FEAT --> DATA
    FEAT --> CORE
    RES --> FEAT
    RES --> DATA
    SIM --> FEAT
    SIM --> DATA
    SIM --> CORE
    METR --> SIM
    METR --> CORE
    REPT --> METR
    REPT --> RES
    EXEC --> CORE
    EXEC --> RES
```

**Regla:** Ningún módulo de nivel superior depende de detalles de implementación de otro módulo del mismo nivel. Toda comunicación pasa por interfaces definidas en `core`.

---

## 4. Ciclo de vida de un experimento

```mermaid
sequenceDiagram
    participant R as Researcher
    participant C as Config
    participant E as Experiment Registry
    participant D as Data Layer
    participant S as Simulation
    participant M as Metrics
    participant Rep as Reports

    R->>C: Define hipótesis + parámetros
    C->>E: Registra experimento (ID, seed, versión)
    E->>D: Solicita datos versionados
    D-->>E: Dataset snapshot
    E->>S: Ejecuta backtest / simulación
    S->>M: Calcula métricas
    M->>Rep: Genera reporte
    Rep-->>R: Resultado reproducible
    R->>E: Cierra experimento (aprobado / rechazado)
```

---

## 5. Separación investigación vs ejecución

```mermaid
flowchart LR
    subgraph QuantLab["QuantLab (investigación)"]
        direction TB
        Q1[Datos]
        Q2[Estrategias]
        Q3[Simulaciones]
        Q4[Alpha Scanner]
        Q5[Reportes]
    end

    subgraph Boundary["Frontera de aprobación"]
        APPR[Aprobación manual / reglas]
    end

    subgraph Runtime["Runtime (ejecución)"]
        direction TB
        R1[Execution Engine]
        R2[Hummingbot]
        R3[Exchange live]
    end

    Q4 --> APPR
    Q5 --> APPR
    APPR -->|config exportada| R1
    R1 --> R2 --> R3
```

QuantLab **nunca** envía órdenes directamente al exchange. Solo exporta configuraciones validadas hacia el Execution Engine.

---

## 6. Escalabilidad de simulaciones (visión futura)

```mermaid
flowchart TB
    ORCH[Orchestrator de simulaciones]
    W1[Worker 1]
    W2[Worker 2]
    WN[Worker N]
    QUEUE[Cola de tareas<br/>futuro: Redis / local]
    STORE[(Result Store — Parquet)]

    ORCH --> QUEUE
    QUEUE --> W1 & W2 & WN
    W1 & W2 & WN --> STORE
    STORE --> MET[Metrics Engine]
```

En Fase inicial: ejecución local secuencial/paralela con `multiprocessing`.
En escalamiento: workers distribuidos sin cambiar interfaces de `Simulator` ni `Optimizer`.
