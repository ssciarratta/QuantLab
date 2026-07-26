# QuantLab — Roadmap alineado (única numeración)

**Fecha:** 2026-07-26  
**Propósito:** Una sola fuente de verdad de fases/módulos para comparar con ChatGPT, AI Studio y el código real.  
**Base de diseño:** [`Arquitectura.md`](Arquitectura.md) §13 (F0–F17) + extensiones producto **F18–F26**  
**Mapa para auditor:** [`docs/audit/MAPA_FASES_PARA_AUDITOR.md`](audit/MAPA_FASES_PARA_AUDITOR.md)  
**Arco nocturno F19–F22:** [`docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md`](audit/INTERNAL_AUDIT_F19_F22_ARC.md) (**APROBADO_INTERNO**)  
**Arco F23–F25:** [`docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md`](audit/INTERNAL_AUDIT_F23_F25_ARC.md) (**APROBADO_INTERNO**)  
**Noche F19–F25:** [`docs/audit/INTERNAL_AUDIT_F19_F25_NIGHT.md`](audit/INTERNAL_AUDIT_F19_F25_NIGHT.md) (**APROBADO_INTERNO**)  
**Noche F19–F26:** [`docs/audit/INTERNAL_AUDIT_F19_F26_NIGHT.md`](audit/INTERNAL_AUDIT_F19_F26_NIGHT.md) (**APROBADO_INTERNO**)  
**F23 Paper Book:** [`docs/audit/INTERNAL_AUDIT_F23.md`](audit/INTERNAL_AUDIT_F23.md) (**APROBADO_INTERNO**)  
**F24 Venue plugins:** [`docs/audit/INTERNAL_AUDIT_F24.md`](audit/INTERNAL_AUDIT_F24.md) (**APROBADO_INTERNO**)  
**F25 Ops Desk:** [`docs/audit/INTERNAL_AUDIT_F25.md`](audit/INTERNAL_AUDIT_F25.md) (**APROBADO_INTERNO**)  
**F26 Paper Session:** [`docs/audit/INTERNAL_AUDIT_F26.md`](audit/INTERNAL_AUDIT_F26.md) (**APROBADO_INTERNO**)  
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
**Estado en repo:** ✅ **APROBADO DEFINITIVO** Meta-Auditor (`docs/audit/FASE_17_APPROVED.md`, 2026-07-25) — incluye residuos F10/F12/F14  
**Extras TD:** Parquet (`ParquetProcessedStore`) + `DuckDBCatalogBackend`  
**Review Package:** `QuantLab_Review_Fase_17_v1.0.zip` · SHA256 `bc875475…`

### Fase 18 — Control Total (research-ops)
**Módulos:**
- FeatureStore anti-colisión de paths (TD-13)
- LogReturn `Decimal.ln` (TD-04)
- Convención TD-17 documentada (`gross_excluding_fees`)
- `LocalPaperLedger` SQLite append-only (sin LIVE)
- Health check + export ops JSON (`quantlab-health`)
- Docs/runbook research-prod

**Estado en repo:** ✅ **APROBADO DEFINITIVO** Meta-Auditor (`docs/audit/FASE_18_APPROVED.md`, 2026-07-25)  
**Bloqueo permanente:** order routing LIVE A3.

### Fase 19 — Operating Modes + BrokerPort
**Módulos:**
- `OperatingMode` TESTER / PAPER / LIVE + `ModeGuard` fail-closed
- Alias producto **REAL = PAPER** (MD/cuenta reales + fills simulados; REAL ≠ LIVE)
- `BrokerPort` Protocol + DTOs neutrales + `BrokerRegistry`
- `PaperBroker` + `PaperFillJournal` (≠ `LocalPaperLedger`)
- Adapter A3 MD-only (`A3BrokerPort`); segundo venue fake `binance`
- Health reporta `operating_mode` + venues
- `docs/ops/LIVE_FLIP_CHECKLIST.md` (flip **no** ejecutado)

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F19.md`, 2026-07-26) — certificado externo `FASE_19_APPROVED.md` **pendiente**  
**Versión:** 0.11.0 · implementación `a5b12d3`  
**Review Package INTERNAL:** `docs/audit/FASE_19_REVIEW_PACKAGE.md`

### Fase 20 — Workbench (1-click / window-manager)
**Módulos:**
- CLI `quantlab-workbench` + `ThreadingHTTPServer` bind default `127.0.0.1`
- JSON API fail-closed ante `OperatingMode.LIVE`; connect siempre `PaperBroker`
- SPA estática + window-manager MDI (drag/resize/minimize/close + taskbar)
- Paneles shell: Health/Mode, Market Data, Paper Blotter (UI ES)
- DEC-061; sin chat (F22), sin paneles F21 (en F20), sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F20.md`, 2026-07-26) — certificado externo `FASE_20_APPROVED.md` **NO emitido**  
**Versión:** 0.12.0 · implementación `cacf8e6`  
**Review Package INTERNAL:** `docs/audit/FASE_20_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F20.md`

### Fase 21 — Lab Panels (workbench features)
**Módulos:**
- `lab_services.py` adapters thin → backtest / scanner / optimizer / MC / features / export-HB / validation / registry
- JSON API `/api/lab/*` (capabilities, metrics, experiments, …)
- 9 paneles SPA + menú Inicio **Laboratorio**
- Export HB path-safe, `live_routing: false`; datos sintéticos / tmp sesión
- DEC-062; sin chat (F22); sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F21.md`, 2026-07-26) — certificado externo `FASE_21_APPROVED.md` **NO emitido**  
**Versión:** 0.13.0 · implementación `c397ffc` · tip lock `0de4211`  
**Review Package INTERNAL:** `docs/audit/FASE_21_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F21.md`

### Fase 22 — Chat IA safe-by-default
**Módulos:**
- `ChatOrchestrator` + `ToolRegistry` allowlist read-only (DEC-063)
- `FakeProvider` default CI + `OptionalEnvProvider` opt-in (DEC-064)
- `ChatAuditLog` JSONL append-only (DEC-065)
- API `POST /api/chat` + `GET /api/chat/tools`; panel Chat IA + banner safe-mode
- Illegal tools (`submit_order`, `set_live`, `place_order`, …) → `ValidationError`
- Sin flip LIVE; sin órdenes venue

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F22.md`, 2026-07-26) — certificado externo `FASE_22_APPROVED.md` **NO emitido**  
**Versión:** 0.14.0 · implementación `5ef9866`  
**Review Package INTERNAL:** `docs/audit/FASE_22_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F22.md`  
**Arco F19–F22:** `docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md` = **APROBADO_INTERNO**

### Fase 23 — Paper Book + Session durable + Risk paper
**Módulos:**
- `PaperBook` (cash/posiciones/avg ponderado/MTM; short fail-closed)
- `PaperBroker` actualiza book; `get_positions` / `get_account` desde book
- `WorkbenchSession` durable bajo `data/runtime/workbench/<id>/` (`validate_session_id`)
- `PaperRiskLimits` (max qty/notional/symbols) en paper submit
- API `GET /api/broker/positions`, `/api/paper/book`, `/api/session`
- Panel Posiciones; DEC-066; sin flip LIVE; sin `md_port.submit`

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F23.md`, 2026-07-26) — certificado externo `FASE_23_APPROVED.md` **NO emitido**  
**Versión:** 0.15.0 · implementación `9b89274`  
**Review Package INTERNAL:** `docs/audit/FASE_23_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F23.md`  
**Remediación audit:** H1 session_id anti-traversal · H2 cash/shorts fail-closed en load (`c846e81`)

### Fase 24 — Venue plugins + MD read-only multiplataforma
**Módulos:**
- Entry points `quantlab.brokers` (`brokers/plugins.py`); builtins + plugins en registry
- A3 `md_source` fake|env (`QUANTLAB_A3_MD_READONLY=1` + creds; fallback fake)
- `generic_csv` / `generic_rest` MD-only; submit/cancel gated
- Workbench `md_provider` / `plugin_venues`; UI Market provider
- DEC-067/068; docs `ops/BROKER_PLUGINS.md`; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F24.md`, 2026-07-26) — certificado externo `FASE_24_APPROVED.md` **NO emitido**  
**Versión:** 0.16.0 · implementación `c846e81`  
**Review Package INTERNAL:** `docs/audit/FASE_24_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F24.md`  
**Remediación audit:** H1 plugins no sombrean builtins (`f8267e3`)  
**Implementation report:** `docs/audit/FASE_24_IMPLEMENTATION_REPORT.md`

### Fase 25 — Ops Desk (1-click + hardening)
**Módulos:**
- `scripts/launch_workbench.sh` + `packaging/quantlab-workbench.desktop` + `docs/ops/WORKBENCH_1CLICK.md`
- CLI `--allow-non-loopback` (cierra M2 non-loopback) + warning stderr
- `validate_experiment_id` charset `^[A-Za-z0-9_-]+$` (cierra M1)
- PaperBroker `slippage_bps` adverso; CLI `--slippage-bps` + connect API
- Panel Riesgo `GET /api/risk` + banner `session_id`; DEC-069
- Sin flip LIVE; sin Electron / auth WAN

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F25.md`, 2026-07-26) — certificado externo `FASE_25_APPROVED.md` **NO emitido**  
**Versión:** 0.17.0 · implementación `21fe144`  
**Review Package INTERNAL:** `docs/audit/FASE_25_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F25.md`  
**Arco F23–F25:** `docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md` = **APROBADO_INTERNO**  
**Noche F19–F25:** `docs/audit/INTERNAL_AUDIT_F19_F25_NIGHT.md` = **APROBADO_INTERNO**  
**Implementation report:** `docs/audit/FASE_25_IMPLEMENTATION_REPORT.md`

### Fase 26 — Paper Session Runner
**Módulos:**
- `PaperSessionRunner` (start/stop/step; background `interval_ms` cancelable)
- Estrategias research: dummy / buy_once / momentum sobre MD snapshot → barras sintéticas
- Risk paper en cada PLACE; submit solo `PaperBroker` (fail-closed isinstance)
- API `/api/paper/session/{start,stop,step,status}`; panel UI “Sesión Paper”
- DEC-070; sin flip LIVE; sin place_order venue; sin WS exchange real

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F26.md`, 2026-07-26) — certificado externo `FASE_26_APPROVED.md` **NO emitido**  
**Versión:** 0.18.0 · implementación `46487a4`  
**Review Package INTERNAL:** `docs/audit/FASE_26_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F26.md`  
**Noche F19–F26:** `docs/audit/INTERNAL_AUDIT_F19_F26_NIGHT.md` = **APROBADO_INTERNO**  
**Remediación audit:** H1 PaperBroker-only en constructor  
**Implementation report:** `docs/audit/FASE_26_IMPLEMENTATION_REPORT.md`

### Fase 27 — Strategy Catalog (workbench)
**Módulos:**
- `workbench/strategy_catalog.py` — metadata + factory + `BarSyntheticBookAdapter` (MM en bar-backtest)
- Wire `InventoryMMStrategy` + `AvellanedaStoikovStrategy` en paper session + lab backtest
- `GET /api/lab/strategies` + `strategy_catalog` en capabilities
- UI selectores + params básicos (Sesión Paper / Backtest)
- DEC-071; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F27.md`, 2026-07-26) — certificado externo `FASE_27_APPROVED.md` **NO emitido**  
**Versión:** 0.19.0 · implementación `244a3fb`  
**Review Package INTERNAL:** `docs/audit/FASE_27_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F27.md`  
**Noche F19–F27:** `docs/audit/INTERNAL_AUDIT_F19_F27_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_27_STRATEGY_CATALOG.md`  
**Implementation report:** `docs/audit/FASE_27_IMPLEMENTATION_REPORT.md`

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

1. F0–F18 certificados externos; F19–F27 **APROBADO_INTERNO** (noche F19–F27).  
2. Certificados externos F19+ solo con APROBADO Meta-Auditor externo (no emitir desde INTERNAL).  
3. LIVE routing sigue **BLOQUEADO**; flip solo con checklist + Meta-Auditor + dueño.
