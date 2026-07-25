# QuantLab — Roadmap alineado (única numeración)

**Fecha:** 2026-07-24  
**Propósito:** Una sola fuente de verdad de fases/módulos para comparar con ChatGPT, AI Studio y el código real.  
**Base de diseño:** [`Arquitectura.md`](Arquitectura.md) §13  
**Estado de ejecución real:** ver columna “Estado en repo”.

> Regla: el cierre formal de cada fase exige Review Package + **APROBADO** del Meta-Auditor.  
> No emitir certificado sin APROBADO real.

---

## Leyenda de estado

| Símbolo | Meaning |
|---------|---------|
| ✅ | Completada y certificada |
| 📦 | Código entregado / Review Package listo — pendiente o en auditoría |
| 🔶 | Parcialmente adelantado en otra etiqueta local |
| ⬜ | No iniciado |

---

## Mapa de fases (oficial alineado)

### Fase 0 — Fundación del repositorio
**Módulos:** estructura de carpetas, tooling, convenciones, LICENSE, README inicial.  
**Estado en repo:** ✅

### Fase 1 — Diseño de arquitectura
**Módulos:** Arquitectura v1.1, DECs, diagramas, roadmap.  
**Estado en repo:** ✅

### Fase 2 — Fundación del dominio, manifests y CI
**Módulos:**
- Tipos de dominio (`frozen` + invariantes)
- Manifests versionados (`DatasetManifest`, `ExperimentManifest`)
- Config + logging
- Contrato `Strategy` / `OrderIntent` (DEC-014)
- CI (ruff, mypy strict, pytest)
- Vertical slice mínimo de infraestructura

**Estado en repo:** ✅ (certificada en proceso de trabajo F2)

### Fase 3 — Datos, catálogo y calidad
**Módulos:**
- Data providers / adapters (en repo: A3 anticorrupción + Fake/pyRofex)
- Raw append-only
- Normalización (barras desde trades)
- Quality checks
- Catálogo local
- Storage processed

**Estado en repo:** ✅ certificada (`docs/audit/FASE_03_APPROVED.md`)  
**Nota:** catálogo SQLite + processed JSONL (DuckDB/Parquet pleno = deuda).

### Fase 4 — Vertical slice + simulación bar MVP + métricas MVP + scanner MVP
> En arquitectura pura, F4 era solo “vertical slice stub”. En la práctica se adelantó investigación mínima.

**Módulos (entregado como F4 local):**
- `BarSimulationEngine` + `ImmediateBarFillModel` + `PortfolioTracker`
- `MetricsEngine` (Sharpe, MDD, win rate, profit factor)
- `AlphaScanner` (ranking vol/volumen/liquidez)
- Slice `quantlab-fase4-slice`

**Estado en repo:** ✅ certificada (`docs/audit/FASE_04_APPROVED.md`)  
**Equivalencia arquitectura:** adelanta partes de F4 + F6 + F8 + F13 (MVP).

### Fase 5 — Features (oficial arquitectura)
**Módulos previstos:**
- Feature transformers (3+)
- Pipeline composable
- Feature store versionado
- Indicators / Feature Pipeline (si se adopta naming ChatGPT)

**Estado en repo:** ✅ certificada (`docs/audit/FASE_05_OFFICIAL_APPROVED.md`)  
**Importante:** el paquete local histórico “Fase 5 ejecución” ≠ Features oficial.  
**Auditoría nocturna:** `docs/audit/NIGHT_AUDIT_2026-07-24.md`

### Fase 6 — Backtester bar-based (5A) completo
**Módulos:**
- FillModel / FeeModel / SlippageModel baseline (parcialmente adelantado)
- Estrategia bar-based
- Golden runs
- Contabilidad cuadrada
- Métricas básicas de simulación

**Estado en repo:** ✅ certificada (`docs/audit/FASE_06_APPROVED.md`)  
**Spec:** `docs/FASE_06_BACKTESTER_5A.md`  
**Auditoría:** `docs/audit/NIGHT_AUDIT_FASE_06_2026-07-24.md`

### Fase 7 — Backtester microestructura (5B)
**Módulos:**
- Market replay (trades/book)
- LatencyModel completo (parcial: fixed bars)
- Fill parcial / cancel / replace
- Inventory para MM
- Slippage book-based

**Estado en repo:** ✅ MVP certificado (`docs/audit/FASE_07_APPROVED.md`)

### Fase 8 — Métricas y reporting
**Módulos:**
- MetricsEngine completo
- ReportGenerator
- Templates HTML
- Contratos neutrales `MetricsResult`

**Estado en repo:** ✅ MVP certificado (`docs/audit/FASE_08_APPROVED.md`)

### Fase 9 — Experiment Registry + artifacts
**Módulos:**
- CRUD experimentos / estados
- Vinculación manifest ↔ artifacts
- Persistencia de resultados

**Estado en repo:** ✅ MVP certificado (`docs/audit/FASE_09_APPROVED.md`)

### Fase 10 — Scientific Validation
**Módulos:**
- Train / validation / OOS
- Walk-forward
- Anti look-ahead / leakage
- Benchmarks y control de overfitting
- Corrección por múltiples comparaciones

**Estado en repo:** ✅ MVP (`docs/audit/FASE_10_TO_16_APPROVED.md`) + corrección múltiple (`bonferroni`/`holm`/`BH`, 2026-07-25)

### Fase 11 — Monte Carlo
**Módulos:** Simulator estocástico, N escenarios, intervalos de confianza, seed fija.  
**Estado en repo:** ✅ MVP (`docs/audit/FASE_10_TO_16_APPROVED.md`)

### Fase 12 — Optimizer (Hyperparameters)
**Módulos:**
- Grid / random search
- Historial de corridas
- Sensibilidad
- Pareto multi-objetivo
- **Dependencia:** F10 aprobada

**Estado en repo:** ✅ MVP grid/random + Pareto (`optimizer/pareto.py`, 2026-07-25)  
**Equivalencia ChatGPT:** “Hyperparameters”

### Fase 13 — Alpha Scanner (completo)
**Módulos:** scanner, ranking, explicabilidad, universo temporal explícito, 10+ activos.  
**Estado en repo:** ✅ MVP + explain (`docs/audit/FASE_10_TO_16_APPROVED.md`)

### Fase 14 — Estrategias avanzadas / Framework de estrategias
**Módulos previstos:**
- BaseStrategy (ampliación del Protocol F2)
- Signal Engine
- Alpha Models
- Position Sizing
- Filters
- Inventory Skew / Adaptive MM / Avellaneda-Stoikov
- **Dependencia fuerte:** F7 para MM

**Estado en repo:** ✅ sizing + InventoryMM + momentum + Avellaneda–Stoikov MVP (2026-07-25)  
**Equivalencia ChatGPT:** gran parte del “Framework de Estrategias” vive aquí (+ F5 Features + F12)

### Fase 15 — Multi-exchange
**Módulos:** provider adicional, normalización cross-exchange, catálogo unificado.  
**Estado en repo:** ✅ MVP `GenericCsvProvider` (+ A3)

### Fase 16 — Hummingbot export (v1)
**Módulos:** validate / build / export package; sin deploy live obligatorio.  
**Estado en repo:** ✅ MVP export (`HummingbotExporter`)  
**Bloqueo permanente hasta decisión:** order routing LIVE.

### Fase 17 — Escalabilidad distribuida
**Módulos:** paralelismo, monitoring, backup, 100K+ simulaciones.  
**Estado en repo:** 📦 código entregado (`docs/audit/FASE_17_IMPLEMENTATION_REPORT.md`) — pendiente APROBADO Meta-Auditor  
**Extras TD:** Parquet (`ParquetProcessedStore`) + `DuckDBCatalogBackend`


---

## Desfase local a resolver (lectura obligatoria)

En el desarrollo reciente se usó esta numeración **local** (no idéntica a Arquitectura §13):

| Etiqueta local | Contenido real | Mapeo a este documento |
|----------------|----------------|------------------------|
| F3 | Data Layer + A3 | ≈ **Fase 3** |
| F4 | Sim + Metrics MVP + AlphaScanner MVP | **Fase 4** + adelanto F6/F8/F13 |
| F5 (código/Review Package) | Slippage, Latency, Fees, Artifacts | Adelanto **F6/F7/F9** — **NO es Fase 5 Features** |

Por eso ChatGPT/AI Studio pueden decir “Fase 5 = Framework de Estrategias / Features” y el repo dice otra cosa: **hubo renumeración práctica**.

**Decisión recomendada para alinear conversaciones externas:**
1. Hablar siempre con la numeración de **este archivo**.
2. Tratar el Review Package `Fase_05` actual como “adelanto de políticas de ejecución / artifacts”, no como Features.
3. La próxima fase de producto tipo ChatGPT (“Framework de Estrategias”) planificarla como **F5 Features + F14 (+ F12)**, no como continuación automática del ZIP F05.

---

## Tabla rápida ChatGPT ↔ Oficial

| Módulo nombrado por ChatGPT | Fase alineada |
|-----------------------------|---------------|
| BaseStrategy | F2 (contrato) + F14 (framework) |
| Indicators / Feature Pipeline | **F5 Features** |
| Signal Engine | F14 |
| Alpha Models | F13–F14 |
| Position Sizing | F6/F7 + F14 |
| Filters | F14 (+ F5) |
| Hyperparameters | **F12 Optimizer** |

---

## Bloqueos globales

- **Order routing real / LIVE A3:** bloqueado (independiente del número de fase).
- **Certificados:** solo con APROBADO explícito del Meta-Auditor.

---

## Próximo paso sugerido

1. Review Package F17 + residuos → Meta-Auditor.  
2. Con **APROBADO** explícito: emitir `FASE_17_APPROVED.md` + sync GitHub.  
3. LIVE routing sigue **BLOQUEADO** hasta decisión de producto.
