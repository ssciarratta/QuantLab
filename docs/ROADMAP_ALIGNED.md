# QuantLab — Roadmap alineado (única numeración)

**Fecha:** 2026-07-26  
**Propósito:** Una sola fuente de verdad de fases/módulos para comparar con ChatGPT, AI Studio y el código real.  
**Base de diseño:** [`Arquitectura.md`](Arquitectura.md) §13 (F0–F17) + extensiones producto **F18–F26**  
**Mapa para auditor:** [`docs/audit/MAPA_FASES_PARA_AUDITOR.md`](audit/MAPA_FASES_PARA_AUDITOR.md)  
**Arco nocturno F19–F22:** [`docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md`](audit/INTERNAL_AUDIT_F19_F22_ARC.md) (**APROBADO_INTERNO**)  
**Arco F23–F25:** [`docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md`](audit/INTERNAL_AUDIT_F23_F25_ARC.md) (**APROBADO_INTERNO**)  
**Noche F19–F25:** [`docs/audit/INTERNAL_AUDIT_F19_F25_NIGHT.md`](audit/INTERNAL_AUDIT_F19_F25_NIGHT.md) (**APROBADO_INTERNO**)  
**Noche F19–F26:** [`docs/audit/INTERNAL_AUDIT_F19_F26_NIGHT.md`](audit/INTERNAL_AUDIT_F19_F26_NIGHT.md) (**APROBADO_INTERNO**)  
**Noche F19–F43:** [`docs/audit/INTERNAL_AUDIT_F19_F43_NIGHT.md`](audit/INTERNAL_AUDIT_F19_F43_NIGHT.md) (**APROBADO_INTERNO**)  
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

### Fase 28 — Layout Persistence + Journal Viewer
**Módulos:**
- `workbench/layout.py` — save/load `layout.json` por sesión (geometría MDI fail-closed)
- API `GET`/`PUT` `/api/layout`; `wm.js` debounce save + restore boot
- Panel Journal (`panes/journal.js`): tabla fills + export CSV client-side
- DEC-072; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F28.md`, 2026-07-26) — certificado externo `FASE_28_APPROVED.md` **NO emitido**  
**Versión:** 0.20.0 · implementación `86517cf`  
**Review Package INTERNAL:** `docs/audit/FASE_28_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F28.md`  
**Noche F19–F28:** `docs/audit/INTERNAL_AUDIT_F19_F28_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_28_LAYOUT_JOURNAL.md`  
**Implementation report:** `docs/audit/FASE_28_IMPLEMENTATION_REPORT.md`

### Fase 29 — Report Viewer + Metrics History
**Módulos:**
- `workbench/reports.py` — persist MetricsResult/summary (+ HTML ReportGenerator) en session `reports/`
- API `GET /api/lab/reports`, `GET /api/lab/reports/{id}`; POST implícito en backtest
- Panel UI Reports: lista + preview HTML|JSON
- DEC-073; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F29.md`, 2026-07-26) — certificado externo `FASE_29_APPROVED.md` **NO emitido**  
**Versión:** 0.21.0 · implementación `2f37bf7`  
**Review Package INTERNAL:** `docs/audit/FASE_29_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F29.md`  
**Noche F19–F29:** `docs/audit/INTERNAL_AUDIT_F19_F29_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_29_REPORTS.md`  
**Implementation report:** `docs/audit/FASE_29_IMPLEMENTATION_REPORT.md`

### Fase 30 — Universe Watchlist + Data Catalog Browser
**Módulos:**
- `workbench/watchlist.py` — `watchlist.json` por sesión (add/remove)
- `workbench/catalog_browser.py` — list read-only vía `quantlab.data.catalog`
- API `GET`/`PUT` `/api/watchlist`, `GET /api/universe`, `GET /api/catalog`
- Paneles UI Universe + Catalog; click símbolo → Market/Session
- DEC-074; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F30.md`, 2026-07-26) — certificado externo `FASE_30_APPROVED.md` **NO emitido**  
**Versión:** 0.22.0 · implementación `7d8bf88`  
**Review Package INTERNAL:** `docs/audit/FASE_30_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F30.md`  
**Noche F19–F30:** `docs/audit/INTERNAL_AUDIT_F19_F30_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_30_UNIVERSE_CATALOG.md`  
**Implementation report:** `docs/audit/FASE_30_IMPLEMENTATION_REPORT.md`

### Fase 31 — Feature Store Browser + Pipeline Runner UI
**Módulos:**
- `workbench/feature_store_browser.py` — list read-only FeatureStore (session/features)
- `lab_services.run_lab_features` — persist vía `FeatureStore.put`
- API `GET /api/lab/features/store`, `POST /api/lab/features/run` (+ alias)
- Panel Features: store + pipeline + columnas
- DEC-075; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F31.md`, 2026-07-26) — certificado externo `FASE_31_APPROVED.md` **NO emitido**  
**Versión:** 0.23.0 · implementación `70a8ee2`  
**Review Package INTERNAL:** `docs/audit/FASE_31_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F31.md`  
**Noche F19–F31:** `docs/audit/INTERNAL_AUDIT_F19_F31_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_31_FEATURES_UI.md`  
**Implementation report:** `docs/audit/FASE_31_IMPLEMENTATION_REPORT.md`

### Fase 32 — Validation / Walk-Forward Runner UI
**Módulos:**
- `workbench/validation_runs.py` — persist session `validation/`
- `lab_services.run_lab_validation` — índices + anti-leakage + persist
- API `POST /api/lab/validation/run`, `GET /api/lab/validation` (+ `/{id}`)
- Panel Validation: splits + leakage + historial
- DEC-076; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F32.md`, 2026-07-26) — certificado externo `FASE_32_APPROVED.md` **NO emitido**  
**Versión:** 0.24.0 · implementación `8c1cf58`  
**Review Package INTERNAL:** `docs/audit/FASE_32_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F32.md`  
**Noche F19–F32:** `docs/audit/INTERNAL_AUDIT_F19_F32_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_32_VALIDATION_UI.md`  
**Implementation report:** `docs/audit/FASE_32_IMPLEMENTATION_REPORT.md`

### Fase 33 — Optimizer History + Pareto Panel
**Módulos:**
- `workbench/optimizer_runs.py` — persist session `optimizer/`
- `lab_services.run_lab_optimize` — grid + métricas + Pareto + persist
- API `POST /api/lab/optimize`, `GET /api/lab/optimize/history` (+ `/{id}`)
- Panel Optimizer: historial + tabla + Pareto (SVG)
- DEC-077; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F33.md`, 2026-07-26) — certificado externo `FASE_33_APPROVED.md` **NO emitido**  
**Versión:** 0.25.0 · implementación `c39a57f`  
**Review Package INTERNAL:** `docs/audit/FASE_33_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F33.md`  
**Noche F19–F33:** `docs/audit/INTERNAL_AUDIT_F19_F33_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_33_OPTIMIZER_UI.md`  
**Implementation report:** `docs/audit/FASE_33_IMPLEMENTATION_REPORT.md`

### Fase 34 — Monte Carlo History + Hummingbot Export Wizard
**Módulos:**
- `workbench/montecarlo_runs.py` — persist session `montecarlo/`
- `workbench/hb_exports.py` — listado path-safe `exports/`
- `lab_services.run_lab_montecarlo` / `run_lab_export_hb` enriquecidos
- API `POST /api/lab/montecarlo`, `GET /api/lab/montecarlo/history`, `GET /api/lab/exports`
- Paneles MC (CI) + Export HB wizard (banner live_routing:false)
- DEC-078; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F34.md`, 2026-07-26) — certificado externo `FASE_34_APPROVED.md` **NO emitido**  
**Versión:** 0.26.0 · implementación `18cea7c`  
**Review Package INTERNAL:** `docs/audit/FASE_34_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F34.md`  
**Noche F19–F34:** `docs/audit/INTERNAL_AUDIT_F19_F34_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_34_MC_EXPORT.md`  
**Implementation report:** `docs/audit/FASE_34_IMPLEMENTATION_REPORT.md`

### Fase 35 — Command Palette + Keyboard Shortcuts
**Módulos:**
- `workbench/commands.py` — registry paneles + acciones seguras
- API `GET /api/commands`
- Command palette SPA (`Ctrl+K` / `Ctrl+Shift+P`) + atajos Ctrl+1..9 / Esc / Ctrl+W
- DEC-079; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F35.md`, 2026-07-26) — certificado externo `FASE_35_APPROVED.md` **NO emitido**  
**Versión:** 0.27.0 · implementación `314b2cd`  
**Review Package INTERNAL:** `docs/audit/FASE_35_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F35.md`  
**Noche F19–F35:** `docs/audit/INTERNAL_AUDIT_F19_F35_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_35_COMMAND_PALETTE.md`  
**Implementation report:** `docs/audit/FASE_35_IMPLEMENTATION_REPORT.md`

### Fase 36 — Settings + Status Bar
**Módulos:**
- `workbench/settings.py` — `settings.json` por sesión
- API `GET/PUT /api/settings`
- Panel Settings + status bar fija (mode, live, session, venue, md, clock)
- Themes `slate` | `high-contrast` · locale `es`
- DEC-080; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F36.md`, 2026-07-26) — certificado externo `FASE_36_APPROVED.md` **NO emitido**  
**Versión:** 0.28.0 · implementación `2c0cb11`  
**Review Package INTERNAL:** `docs/audit/FASE_36_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F36.md`  
**Noche F19–F36:** `docs/audit/INTERNAL_AUDIT_F19_F36_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_36_SETTINGS.md`  
**Implementation report:** `docs/audit/FASE_36_IMPLEMENTATION_REPORT.md`

### Fase 37 — First-run Onboarding Wizard
**Módulos:**
- `workbench/onboarding.py` — `onboarding_done` en session `meta.json`
- API `GET /api/onboarding` + `POST /api/onboarding/complete`
- Wizard modal 4 pasos (modos · venue tester · Paper/Backtest · Chat IA)
- DEC-081; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F37.md`, 2026-07-26) — certificado externo `FASE_37_APPROVED.md` **NO emitido**  
**Versión:** 0.29.0 · implementación `81ff9b1`  
**Review Package INTERNAL:** `docs/audit/FASE_37_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F37.md`  
**Noche F19–F37:** `docs/audit/INTERNAL_AUDIT_F19_F37_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_37_ONBOARDING.md`  
**Implementation report:** `docs/audit/FASE_37_IMPLEMENTATION_REPORT.md`

### Fase 38 — Docs / Help Browser
**Módulos:**
- `workbench/docs_browser.py` — lista/lee `docs/*.md` + `docs/ops/*.md` fail-closed
- API `GET /api/docs` + `GET /api/docs/content?path=`
- Panel Help/Docs (buscar + preview HTML escapado | pre)
- Chat `search_docs` incluye ops/; DEC-082; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F38.md`, 2026-07-26) — certificado externo `FASE_38_APPROVED.md` **NO emitido**  
**Versión:** 0.30.0 · implementación `becd116`  
**Review Package INTERNAL:** `docs/audit/FASE_38_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F38.md`  
**Noche F19–F38:** `docs/audit/INTERNAL_AUDIT_F19_F38_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_38_DOCS_HELP.md`  
**Implementation report:** `docs/audit/FASE_38_IMPLEMENTATION_REPORT.md`

### Fase 39 — Session Export/Import ZIP
**Módulos:**
- `workbench/session_zip.py` — export/import ZIP sin secretos + zip-slip fail-closed
- API `GET /api/session/export` (+ `?download=1`) + `POST /api/session/import` (new|merge)
- UI Export/Import en Settings; DEC-083; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F39.md`, 2026-07-26) — certificado externo `FASE_39_APPROVED.md` **NO emitido**  
**Versión:** 0.31.0 · implementación `0cb9d7a`  
**Review Package INTERNAL:** `docs/audit/FASE_39_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F39.md`  
**Noche F19–F39:** `docs/audit/INTERNAL_AUDIT_F19_F39_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_39_SESSION_ZIP.md`  
**Implementation report:** `docs/audit/FASE_39_IMPLEMENTATION_REPORT.md`

### Fase 40 — Workspace Presets
**Módulos:**
- `workbench/presets.py` — presets built-in research / trading_paper / ops
- API `GET /api/presets` + `POST /api/presets/apply` → `layout.json`
- UI menú Inicio → Espacios de trabajo; DEC-084; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F40.md`, 2026-07-26) — certificado externo `FASE_40_APPROVED.md` **NO emitido**  
**Versión:** 0.32.0 · implementación `8197f32`  
**Review Package INTERNAL:** `docs/audit/FASE_40_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F40.md`  
**Noche F19–F40:** `docs/audit/INTERNAL_AUDIT_F19_F40_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_40_PRESETS.md`  
**Implementation report:** `docs/audit/FASE_40_IMPLEMENTATION_REPORT.md`

### Fase 41 — Activity Log + Toasts
**Módulos:**
- `workbench/activity.py` — activity.jsonl append-only (connect/submit/backtest/optimize/export/error)
- API `GET /api/activity?limit=100` + hooks handlers clave
- UI toasts success/error + panel Activity; DEC-085; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F41.md`, 2026-07-26) — certificado externo `FASE_41_APPROVED.md` **NO emitido**  
**Versión:** 0.33.0 · implementación `f1db945`  
**Review Package INTERNAL:** `docs/audit/FASE_41_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F41.md`  
**Noche F19–F41:** `docs/audit/INTERNAL_AUDIT_F19_F41_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_41_ACTIVITY.md`  
**Implementation report:** `docs/audit/FASE_41_IMPLEMENTATION_REPORT.md`

### Fase 42 — Ops Metrics Panel
**Módulos:**
- `infra/ops_metrics.py` — contadores in-process + Prometheus text (reutilizado)
- API `GET /api/ops/metrics` (JSON) + `GET /api/ops/prometheus` (text/plain)
- UI panel Ops Metrics (tabla + highlight `live_gate.blocked`); DEC-086; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F42.md`, 2026-07-26) — certificado externo `FASE_42_APPROVED.md` **NO emitido**  
**Versión:** 0.34.0 · implementación `34bfac5`  
**Review Package INTERNAL:** `docs/audit/FASE_42_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F42.md`  
**Noche F19–F42:** `docs/audit/INTERNAL_AUDIT_F19_F42_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_42_OPS_METRICS.md`  
**Implementation report:** `docs/audit/FASE_42_IMPLEMENTATION_REPORT.md`

### Fase 43 — Red-team Workbench Hardening
**Módulos:**
- Auditoría red-team APIs workbench (`api.py` / `server.py` / session paths)
- Remediación fail-closed: `zip_path` sandbox, `create_server` loopback gate, body 2 MiB, `csv_path` anti-traversal
- Tests `test_redteam_f43.py`; DEC-087; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F43.md`, 2026-07-26) — certificado externo `FASE_43_APPROVED.md` **NO emitido**  
**Versión:** 0.35.0 · implementación `2b90b1f`  
**Review Package INTERNAL:** `docs/audit/FASE_43_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F43.md`  
**Noche F19–F43:** `docs/audit/INTERNAL_AUDIT_F19_F43_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_43_REDTEAM.md`  
**Implementation report:** `docs/audit/FASE_43_IMPLEMENTATION_REPORT.md`

### Fase 44 — E2E Paper Workflow Integration Test
**Módulos:**
- Test integración HTTP loopback (sin browser) del flujo paper completo
- Encadena mode/connect/submit/session/lab/export/zip + LIVE reject
- DEC-088; bump 0.36.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F44.md`, 2026-07-26) — certificado externo `FASE_44_APPROVED.md` **NO emitido**  
**Versión:** 0.36.0 · implementación `df89295`  
**Review Package INTERNAL:** `docs/audit/FASE_44_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F44.md`  
**Noche F19–F44:** `docs/audit/INTERNAL_AUDIT_F19_F44_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_44_E2E_WORKFLOW.md`  
**Implementation report:** `docs/audit/FASE_44_IMPLEMENTATION_REPORT.md`

### Fase 45 — About Dialog + Version Badge
**Módulos:**
- `GET /api/about` (version, live_blocked, phases_summary, python, bind_policy)
- Badge versión en status bar + diálogo Acerca de (Inicio / command palette)
- DEC-089; bump 0.37.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F45.md`, 2026-07-26) — certificado externo `FASE_45_APPROVED.md` **NO emitido**  
**Versión:** 0.37.0 · implementación `a103236`  
**Review Package INTERNAL:** `docs/audit/FASE_45_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F45.md`  
**Noche F19–F45:** `docs/audit/INTERNAL_AUDIT_F19_F45_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_45_ABOUT.md`  
**Implementation report:** `docs/audit/FASE_45_IMPLEMENTATION_REPORT.md`

### Fase 46 — Multi-Session Switcher
**Módulos:**
- `GET /api/sessions` + `POST /api/sessions/switch` + `POST /api/sessions/new`
- UI panel Sessions (Inicio / command palette); `validate_session_id` fail-closed
- DEC-090; bump 0.38.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F46.md`, 2026-07-26) — certificado externo `FASE_46_APPROVED.md` **NO emitido**  
**Versión:** 0.38.0 · implementación `ce9cbdd`  
**Review Package INTERNAL:** `docs/audit/FASE_46_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F46.md`  
**Noche F19–F46:** `docs/audit/INTERNAL_AUDIT_F19_F46_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_46_SESSIONS.md`  
**Implementation report:** `docs/audit/FASE_46_IMPLEMENTATION_REPORT.md`

### Fase 47 — Chat Context Awareness
**Módulos:**
- ToolRegistry allowlist: `get_session_summary`, `list_reports`, `list_strategies` (read-only)
- FakeProvider intents ES (cómo estoy / resumen sesión / reportes / estrategias)
- DEC-091; bump 0.39.0; sin flip LIVE; chat sin trading tools

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F47.md`, 2026-07-26) — certificado externo `FASE_47_APPROVED.md` **NO emitido**  
**Versión:** 0.39.0 · implementación `afdf067`  
**Review Package INTERNAL:** `docs/audit/FASE_47_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F47.md`  
**Noche F19–F47:** `docs/audit/INTERNAL_AUDIT_F19_F47_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_47_CHAT_CONTEXT.md`  
**Implementation report:** `docs/audit/FASE_47_IMPLEMENTATION_REPORT.md`

### Fase 48 — Theme CSS Completion (slate + high-contrast)
**Módulos:**
- Tokens CSS completos `slate` | `high-contrast` (chrome + semantic) en `workbench.css`
- `data-theme` en `documentElement` (+ body) al load settings y PUT `/api/settings`
- DEC-092; bump 0.40.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F48.md`, 2026-07-26) — certificado externo `FASE_48_APPROVED.md` **NO emitido**  
**Versión:** 0.40.0 · implementación `9227750`  
**Review Package INTERNAL:** `docs/audit/FASE_48_REVIEW_PACKAGE.md`  
**Autauditoría:** `docs/audit/AUTO_AUDIT_2026-07-26_F48.md`  
**Noche F19–F48:** `docs/audit/INTERNAL_AUDIT_F19_F48_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_48_THEMES.md`  
**Implementation report:** `docs/audit/FASE_48_IMPLEMENTATION_REPORT.md`

### Fase 49 — Milestone Freeze Docs + CHANGELOG Sync
**Módulos:**
- Freeze documental F19–F48 (`MILESTONE_V040_FREEZE.md`): inventario, invariantes, operar, límites no LIVE
- Sync CHANGELOG (resumen agrupado) + RESUMEN + PROJECT_MEMORY + README
- Smoke About `version` ≡ `__version__`; bundle default F19–F49
- DEC-093; bump 0.41.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F49.md`, 2026-07-26) — certificado externo `FASE_49_APPROVED.md` **NO emitido**  
**Versión:** 0.41.0 · implementación `0ddbe67`  
**Freeze:** `docs/audit/MILESTONE_V040_FREEZE.md`  
**Noche F19–F49:** `docs/audit/INTERNAL_AUDIT_F19_F49_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_49_MILESTONE.md`  
**Implementation report:** `docs/audit/FASE_49_IMPLEMENTATION_REPORT.md`

### Fase 50 — Performance Baseline Workbench API
**Módulos:**
- `quantlab.workbench.perf_baseline` — p50/p95/max loopback de endpoints clave
- Suite + CLI: health, mode, commands, about, lab/capabilities (p95/max < 500ms)
- DEC-094; bump 0.42.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F50.md`, 2026-07-26) — certificado externo `FASE_50_APPROVED.md` **NO emitido**  
**Versión:** 0.42.0 · implementación `d91f239`  
**Noche F19–F50:** `docs/audit/INTERNAL_AUDIT_F19_F50_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_50_PERF_BASELINE.md`  
**Implementation report:** `docs/audit/FASE_50_IMPLEMENTATION_REPORT.md`

### Fase 51 — API Rate Limit (loopback soft)
**Módulos:**
- `quantlab.workbench.rate_limit` — token bucket in-process por IP/path
- Soft 429 JSON en workbench `server.py` (default 120 req/s; inyectable)
- DEC-095; bump 0.43.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F51.md`, 2026-07-26) — certificado externo `FASE_51_APPROVED.md` **NO emitido**  
**Versión:** 0.43.0 · implementación `2451802`  
**Noche F19–F51:** `docs/audit/INTERNAL_AUDIT_F19_F51_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_51_RATE_LIMIT.md`  
**Implementation report:** `docs/audit/FASE_51_IMPLEMENTATION_REPORT.md`

### Fase 52 — Graceful Shutdown + Paper Session Safety
**Módulos:**
- `quantlab.workbench.shutdown` — stop paper + flush layout/settings/book + flag
- SIGINT/SIGTERM en `launch.py`; `POST /api/shutdown` loopback-only
- DEC-096; bump 0.44.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F52.md`, 2026-07-26) — certificado externo `FASE_52_APPROVED.md` **NO emitido**  
**Versión:** 0.44.0 · implementación `feace00`  
**Noche F19–F52:** `docs/audit/INTERNAL_AUDIT_F19_F52_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_52_SHUTDOWN.md`  
**Implementation report:** `docs/audit/FASE_52_IMPLEMENTATION_REPORT.md`

### Fase 53 — Dockerfile Workbench (opt-in)
**Módulos / artefactos:**
- `Dockerfile.workbench` — python 3.12-slim + uv sync · EXPOSE 8765
- CMD `--host 0.0.0.0 --allow-non-loopback --no-browser` (riesgo documentado; port-map)
- `.dockerignore` · `docs/ops/DOCKER_WORKBENCH.md`
- DEC-097; bump 0.45.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F53.md`, 2026-07-26) — certificado externo `FASE_53_APPROVED.md` **NO emitido**  
**Versión:** 0.45.0 · implementación `065821b`  
**Noche F19–F53:** `docs/audit/INTERNAL_AUDIT_F19_F53_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_53_DOCKER.md`  
**Implementation report:** `docs/audit/FASE_53_IMPLEMENTATION_REPORT.md`

### Fase 54 — Readiness / Liveness Probes
**Módulos:**
- `quantlab.workbench.probes` — livez/readyz payload + session-root writable check
- `GET /api/livez` · `GET /api/readyz` (200/503) en server/api
- Ops HEALTHCHECK en `docs/ops/DOCKER_WORKBENCH.md`
- DEC-098; bump 0.46.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F54.md`, 2026-07-26) — certificado externo `FASE_54_APPROVED.md` **NO emitido**  
**Versión:** 0.46.0 · implementación `a34902c`  
**Noche F19–F54:** `docs/audit/INTERNAL_AUDIT_F19_F54_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_54_PROBES.md`  
**Implementation report:** `docs/audit/FASE_54_IMPLEMENTATION_REPORT.md`

### Fase 55 — OpenAPI / API Catalog
**Módulos:**
- `quantlab.workbench.api_catalog` — catálogo estático + OpenAPI 3 mínimo (sin FastAPI)
- `GET /api/openapi.json` en server/api
- Link About → API (OpenAPI)
- DEC-099; bump 0.47.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F55.md`, 2026-07-26) — certificado externo `FASE_55_APPROVED.md` **NO emitido**  
**Versión:** 0.47.0 · implementación `b415978`  
**Noche F19–F55:** `docs/audit/INTERNAL_AUDIT_F19_F55_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_55_OPENAPI.md`  
**Implementation report:** `docs/audit/FASE_55_IMPLEMENTATION_REPORT.md`

### Fase 56 — Security Headers
**Módulos:**
- `quantlab.workbench.security_headers` — nosniff / DENY / no-referrer; Cache-Control no-store en `/api/*`
- CORS fail-closed: nunca `Access-Control-Allow-Origin: *`; Origin non-loopback no se refleja
- Integración en `server.py` (`_apply_security_headers`)
- DEC-100; bump 0.48.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F56.md`, 2026-07-26) — certificado externo `FASE_56_APPROVED.md` **NO emitido**  
**Versión:** 0.48.0 · implementación `6246a74`  
**Noche F19–F56:** `docs/audit/INTERNAL_AUDIT_F19_F56_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_56_SECURITY_HEADERS.md`  
**Implementation report:** `docs/audit/FASE_56_IMPLEMENTATION_REPORT.md`

### Fase 57 — Content-Security-Policy
**Módulos:**
- `quantlab.workbench.security_headers.CONTENT_SECURITY_POLICY` — CSP restrictiva SPA local
- Política: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'`
- Sin `unsafe-eval`; HTML sin scripts inline (externos `/static/js`)
- DEC-101; bump 0.49.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F57.md`, 2026-07-26) — certificado externo `FASE_57_APPROVED.md` **NO emitido**  
**Versión:** 0.49.0 · implementación `fbb0355`  
**Noche F19–F57:** `docs/audit/INTERNAL_AUDIT_F19_F57_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_57_CSP.md`  
**Implementation report:** `docs/audit/FASE_57_IMPLEMENTATION_REPORT.md`

### Fase 58 — Milestone Freeze Docs + CHANGELOG Sync (v0.50)
**Alcance:**
- Freeze documental F19–F57/F58 (`MILESTONE_V050_FREEZE.md`): inventario, invariantes, operar, límites no LIVE
- Sync CHANGELOG (resumen agrupado F19–F57) · RESUMEN · PROJECT_MEMORY · README
- Smoke tip version **starts with 0.50**; bundle default F19–F58
- DEC-102; bump 0.50.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F58.md`, 2026-07-26) — certificado externo `FASE_58_APPROVED.md` **NO emitido**  
**Versión:** 0.50.0 · implementación `7f6c440`  
**Freeze:** `docs/audit/MILESTONE_V050_FREEZE.md`  
**Noche F19–F58:** `docs/audit/INTERNAL_AUDIT_F19_F58_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_58_MILESTONE_V050.md`  
**Implementation report:** `docs/audit/FASE_58_IMPLEMENTATION_REPORT.md`

### Fase 59 — A11y Basics (focus + aria)
**Alcance:**
- `role="dialog"` + `aria-modal` + `aria-label` en palette / about / onboarding
- `aria-label` en botones taskbar; focus trap Tab en Command Palette
- Skip link «Ir al contenido» → `#workspace`
- DEC-103; bump 0.51.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F59.md`, 2026-07-26) — certificado externo `FASE_59_APPROVED.md` **NO emitido**  
**Versión:** 0.51.0 · implementación `6a1823a`  
**Noche F19–F59:** `docs/audit/INTERNAL_AUDIT_F19_F59_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_59_A11Y.md`  
**Implementation report:** `docs/audit/FASE_59_IMPLEMENTATION_REPORT.md`

### Fase 60 — i18n Scaffold (es default)
**Alcance:**
- Diccionario UI es (default) + stub en (`static/js/i18n.js` · `static/i18n/*.json`)
- Shell aplica `settings.locale` vía `QLi18n.t()` / `applyDom` al load
- `GET /api/i18n/{locale}` opcional; OpenAPI catalog
- DEC-104; bump 0.52.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F60.md`, 2026-07-26) — certificado externo `FASE_60_APPROVED.md` **NO emitido**  
**Versión:** 0.52.0 · implementación `f7506c7`  
**Noche F19–F60:** `docs/audit/INTERNAL_AUDIT_F19_F60_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_60_I18N.md`  
**Implementation report:** `docs/audit/FASE_60_IMPLEMENTATION_REPORT.md`

### Fase 61 — Workbench Request Access Log
**Alcance:**
- `access.jsonl` append-only por sesión (method, path, status, ms) — sin bodies/secrets
- Settings `access_log: true` (default) · toggle UI
- `GET /api/access-log?limit=100`; middleware server
- DEC-105; bump 0.53.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F61.md`, 2026-07-26) — certificado externo `FASE_61_APPROVED.md` **NO emitido**  
**Versión:** 0.53.0 · implementación `15e1707`  
**Noche F19–F61:** `docs/audit/INTERNAL_AUDIT_F19_F61_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_61_ACCESS_LOG.md`  
**Implementation report:** `docs/audit/FASE_61_IMPLEMENTATION_REPORT.md`

### Fase 62 — Access Log Panel UI
**Alcance:**
- Panel SPA Access Log consumiendo `GET /api/access-log` (F61)
- Menú Inicio → Sistema → Access Log · command palette `open.access_log`
- Auto-refresh opcional (5s) + dispose al cerrar
- DEC-106; bump 0.54.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F62.md`, 2026-07-26) — certificado externo `FASE_62_APPROVED.md` **NO emitido**  
**Versión:** 0.54.0 · implementación `7065400`  
**Noche F19–F62:** `docs/audit/INTERNAL_AUDIT_F19_F62_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_62_ACCESS_LOG_UI.md`  
**Implementation report:** `docs/audit/FASE_62_IMPLEMENTATION_REPORT.md`

### Fase 63 — Session Auto-Backup
**Alcance:**
- Settings `auto_backup_minutes` (default 0=off); scheduler → `session/backups/` rotación max 5
- `GET /api/backups`; reusa `session_zip` allowlist + zip-slip; `run_auto_backup` manual
- DEC-107; bump 0.55.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F63.md`, 2026-07-26) — certificado externo `FASE_63_APPROVED.md` **NO emitido**  
**Versión:** 0.55.0  
**Noche F19–F63:** `docs/audit/INTERNAL_AUDIT_F19_F63_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_63_AUTO_BACKUP.md`  
**Implementation report:** `docs/audit/FASE_63_IMPLEMENTATION_REPORT.md`

### Fase 64 — Backups Panel UI
**Alcance:**
- Panel SPA Backups consumiendo `GET /api/backups` + `POST /api/backups/run`
- Menú Inicio → Sistema → Backups · command palette `open.backups`
- Botón **Backup ahora** (trigger manual `run_auto_backup`)
- DEC-108; bump 0.56.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F64.md`, 2026-07-26) — certificado externo `FASE_64_APPROVED.md` **NO emitido**  
**Versión:** 0.56.0  
**Noche F19–F64:** `docs/audit/INTERNAL_AUDIT_F19_F64_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_64_BACKUPS_UI.md`  
**Implementation report:** `docs/audit/FASE_64_IMPLEMENTATION_REPORT.md`

### Fase 65 — Blotter CSV Server Export
**Alcance:**
- `GET /api/paper/fills.csv` — text/csv de fills del journal paper
- Botón **Descargar CSV** en Blotter y Journal
- DEC-109; bump 0.57.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F65.md`, 2026-07-26) — certificado externo `FASE_65_APPROVED.md` **NO emitido**  
**Versión:** 0.57.0  
**Noche F19–F65:** `docs/audit/INTERNAL_AUDIT_F19_F65_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_65_BLOTTER_CSV.md`  
**Implementation report:** `docs/audit/FASE_65_IMPLEMENTATION_REPORT.md`

### Fase 66 — Equity Curve Snapshot
**Alcance:**
- Session `equity.jsonl` append (`ts`, `equity`, `cash`) en fills + paper session step
- `GET /api/paper/equity?limit=N` — últimos N puntos
- Sección Equity curve en Positions (lista + sparkline SVG)
- DEC-110; bump 0.58.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F66.md`, 2026-07-26) — certificado externo `FASE_66_APPROVED.md` **NO emitido**  
**Versión:** 0.58.0  
**Noche F19–F66:** `docs/audit/INTERNAL_AUDIT_F19_F66_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_66_EQUITY.md`  
**Implementation report:** `docs/audit/FASE_66_IMPLEMENTATION_REPORT.md`

### Fase 67 — Paper PnL Summary
**Alcance:**
- `PaperBook.get_pnl` — realized/unrealized/equity/cash desde book + marks
- `GET /api/paper/pnl` — marks broker o avg fallback
- Headers PnL en Positions y Blotter
- DEC-111; bump 0.59.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F67.md`, 2026-07-26) — certificado externo `FASE_67_APPROVED.md` **NO emitido**  
**Versión:** 0.59.0  
**Noche F19–F67:** `docs/audit/INTERNAL_AUDIT_F19_F67_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_67_PNL.md`  
**Implementation report:** `docs/audit/FASE_67_IMPLEMENTATION_REPORT.md`

### Fase 68 — Milestone Freeze Docs + CHANGELOG Sync (v0.60)
**Alcance:**
- Freeze documental F19–F67/F68 (`MILESTONE_V060_FREEZE.md`): inventario, invariantes, operar, límites no LIVE
- Sync CHANGELOG (resumen agrupado F19–F67) · RESUMEN · PROJECT_MEMORY · README
- Smoke tip version **starts with 0.60**; bundle default F19–F68
- DEC-112; bump 0.60.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F68.md`, 2026-07-26) — certificado externo `FASE_68_APPROVED.md` **NO emitido**  
**Versión:** 0.60.0 · implementación `140eb25`  
**Freeze:** `docs/audit/MILESTONE_V060_FREEZE.md`  
**Noche F19–F68:** `docs/audit/INTERNAL_AUDIT_F19_F68_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_68_MILESTONE_V060.md`  
**Implementation report:** `docs/audit/FASE_68_IMPLEMENTATION_REPORT.md`

### Fase 69 — Risk Utilization Report
**Alcance:**
- `GET /api/risk/utilization` — % used max_qty/notional vs PaperBook posiciones
- Sección Utilización en panel Risk (peak qty + gross notional)
- DEC-113; bump 0.61.0; sin flip LIVE

**Estado en repo:** 📦 ✅ **APROBADO_INTERNO** (`docs/audit/INTERNAL_AUDIT_F69.md`, 2026-07-26) — certificado externo `FASE_69_APPROVED.md` **NO emitido**  
**Versión:** 0.61.0  
**Noche F19–F69:** `docs/audit/INTERNAL_AUDIT_F19_F69_NIGHT.md` = **APROBADO_INTERNO**  
**Spec:** `docs/FASE_69_RISK_UTIL.md`  
**Implementation report:** `docs/audit/FASE_69_IMPLEMENTATION_REPORT.md`

---


## Fase 70 — Paper Kill Switch

**Versión:** 0.62.0 · **DEC-114** · **APROBADO_INTERNO** (sin `FASE_70_APPROVED.md`)

- Kill switch paper-only: `meta.paper_kill_engaged`
- When engaged → reject paper submit + session step (`ValidationError`)
- API `GET`/`POST /api/paper/kill`
- Big red ENGAGE/DISENGAGE en Risk + Sesión Paper
- Smoke About≡`__version__` 0.62.0; bundle default F19–F70
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 71 — Health Extended + 1000 Tests Milestone

**Versión:** 0.63.0 · **DEC-115** · **APROBADO_INTERNO** (sin `FASE_71_APPROVED.md`)

- Extiende `GET /api/health` + `GET /api/about` con flags: `paper_kill_engaged`, `auto_backup_minutes`, `access_log`
- Suite `test_health_extended_f71.py` (edge cases útiles) → **≥1000 pytest passed**
- Health pane + About UI surface ops flags
- Smoke F71; bundle INTERNAL default F19–F71
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 72 — Desktop Notifications Hook

**Versión:** 0.64.0 · **DEC-116** · **APROBADO_INTERNO** (sin `FASE_72_APPROVED.md`)

- Settings `desktop_notifications` (default **false**) · checkbox UI
- Cuando true → JS Notification API en toast errors + kill engage (graceful si denied)
- Smoke F72; bundle INTERNAL default F19–F72
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 73 — Optional Sound Alerts

**Versión:** 0.65.0 · **DEC-117** · **APROBADO_INTERNO** (sin `FASE_73_APPROVED.md`)

- Settings `sound_alerts` (default **false**) · checkbox UI
- Cuando true → WebAudio beep corto en toast errors + kill engage (sin assets externos)
- Smoke F73; bundle INTERNAL default F19–F73
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 74 — Status Bar Clock Timezone

**Versión:** 0.66.0 · **DEC-118** · **APROBADO_INTERNO** (sin `FASE_74_APPROVED.md`)

- Settings `timezone` (default **UTC**; opciones `UTC` / `local`) · select UI
- Status bar clock respeta setting (JS `toLocaleTimeString` + `timeZone`)
- Smoke F74; bundle INTERNAL default F19–F74
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 75 — Broker Heartbeat Status

**Versión:** 0.67.0 · **DEC-119** · **APROBADO_INTERNO** (sin `FASE_75_APPROVED.md`)

- `GET /api/broker/heartbeat` — `broker.health()` si conectado; else `disconnected`
- Status bar ok/fail · shell poll **N=5** s
- Smoke F75; bundle INTERNAL default F19–F75
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 76 — Broker Reconnect Button

**Versión:** 0.68.0 · **DEC-120** · **APROBADO_INTERNO** (sin `FASE_76_APPROVED.md`)

- `POST /api/broker/reconnect` — re-run last connect params from session meta
- Persist `last_broker_connect` en `meta.json` al connect
- UI botón Reconectar en Market + Health
- Smoke F76; bundle INTERNAL default F19–F76
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 77 — Broker Disconnect + Milestone prep

**Versión:** 0.69.0 · **DEC-121** · **APROBADO_INTERNO** (sin `FASE_77_APPROVED.md`)

- `POST /api/broker/disconnect` — close broker, clear connected state, keep last_connect
- UI botón Desconectar en Market + Health
- Smoke F77; bundle INTERNAL default F19–F77; prep v0.70
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 78 — Milestone Freeze Docs + CHANGELOG Sync (v0.70)

**Versión:** 0.70.0 · **DEC-122** · **APROBADO_INTERNO** (sin `FASE_78_APPROVED.md`)

- Freeze documental `docs/audit/MILESTONE_V070_FREEZE.md` (inventario F19–F77/F78)
- Sync tip: CHANGELOG (resumen F19–F77) · RESUMEN · PROJECT_MEMORY · README
- Smoke: version **starts with 0.70**; bundle INTERNAL default F19–F78
- `LIVE_BLOCKED=True`; sin flip LIVE · **hito 0.70**


## Fase 79 — Watchlist Import/Export JSON

**Versión:** 0.71.0 · **DEC-123** · **APROBADO_INTERNO** (sin `FASE_79_APPROVED.md`)

- `GET /api/watchlist/export` — JSON download (Content-Disposition)
- `POST /api/watchlist/import` — `{symbols, mode: merge|replace}`
- UI Universe: Export JSON / Import JSON
- Smoke F79; bundle INTERNAL default F19–F79
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 80 — Custom Preset Save

**Versión:** 0.72.0 · **DEC-124** · **APROBADO_INTERNO** (sin `FASE_80_APPROVED.md`)

- `POST /api/presets/save` `{name}` — guarda layout actual en `session/presets/{name}.json`
- `GET /api/presets` incluye custom (`custom: true`)
- `POST /api/presets/apply` aplica también presets custom
- UI Inicio: Guardar espacio actual… + lista custom
- Smoke F80; bundle INTERNAL default F19–F80
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 81 — Custom Preset Delete

**Versión:** 0.73.0 · **DEC-125** · **APROBADO_INTERNO** (sin `FASE_81_APPROVED.md`)

- `DELETE /api/presets/{name}` — borra solo presets custom de sesión
- Built-ins `research|trading_paper|ops` protegidos (400)
- UI Inicio: × en filas custom (`data-preset-delete`)
- Smoke F81; bundle INTERNAL default F19–F81
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 82 — Window Snap to Edges

**Versión:** 0.74.0 · **DEC-126** · **APROBADO_INTERNO** (sin `FASE_82_APPROVED.md`)

- Al soltar drag: `snapPosition` a bordes/viewport si distancia < 12px
- Persist layout (`scheduleSave`) post-snap
- Espejo Python `snap_position` + suite/smoke F82
- Bundle INTERNAL default F19–F82
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 83 — Minimize / Restore All

**Versión:** 0.75.0 · **DEC-127** · **APROBADO_INTERNO** (sin `FASE_83_APPROVED.md`)

- Command palette + menú: Minimize all / Restore all windows
- `wm.js` `minimizeAll` / `restoreAll` + `scheduleSave` (persist `minimized`)
- Suite/smoke F83; bundle INTERNAL default F19–F83
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 84 — Cascade / Tile Windows

**Versión:** 0.76.0 · **DEC-128** · **APROBADO_INTERNO** (sin `FASE_84_APPROVED.md`)

- Command palette + menú: Cascade windows / Tile windows
- `wm.js` `cascadeWindows` / `tileWindows` + pure rects + `scheduleSave`
- Espejo Python `window_layout` + suite/smoke F84
- Bundle INTERNAL default F19–F84
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 85 — Bring to Front / Send to Back

**Versión:** 0.77.0 · **DEC-129** · **APROBADO_INTERNO** (sin `FASE_85_APPROVED.md`)

- Command palette + menú + context titlebar: Bring to Front / Send to Back
- `wm.js` `bringToFront` / `sendToBack` + `scheduleSave` (persist `z`)
- Restore `z` on open via `mergeOpts` / layout
- Suite/smoke F85; bundle INTERNAL default F19–F85
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 86 — Maximize / Restore Window

**Versión:** 0.78.0 · **DEC-130** · **APROBADO_INTERNO** (sin `FASE_86_APPROVED.md`)

- Command palette + menú + titlebar btn/dblclick: Maximize / Restore
- `wm.js` `maximize` / `restoreFromMaximize` / `toggleMaximize` + store `preMax`
- Persist `maximized` in layout; restore on open via `mergeOpts`
- Suite/smoke F86; bundle INTERNAL default F19–F86
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 87 — Broker Plugin Contract v1

**Versión:** 0.79.0 · **DEC-131** · **APROBADO_INTERNO** (sin `FASE_87_APPROVED.md`)

- `BrokerPluginSpec` API `"1"` con venue y capabilities read-only validados
- Capabilities permitidas: `market_data`, `account_read`; ejecución prohibida
- `ReadOnlyBrokerPort` obligatorio para plugins externos
- Registry valida firma y llama factory una sola vez, sin retry de `TypeError`
- Entry point v1 + legacy v0 con warning; no shadow de builtins
- Test kit cooperativo/offline; no es sandbox contra plugin malicioso
- Suite adversarial + smoke F87; bundle INTERNAL default F19–F87
- `LIVE_BLOCKED=True`; sin flip LIVE


## Fase 88 — Paper Journal authoritative + Book reconciliation

**Versión:** 0.80.0 · **DEC-132** · **APROBADO_INTERNO** (sin `FASE_88_APPROVED.md`)

- `journal.jsonl` append-only es source of truth; reader estricto y duplicados rechazados
- `book.json` v2 es proyección atómica ligada a checkpoint SHA-256
- PaperBroker hace preview y commit journal → book → persist; falla post-journal bloquea
- Boot fail-closed: journal-ahead/mismatch/corrupción requieren rebuild explícito
- CLI offline `--check|--rebuild`, con backup de book y journal inmutable
- `GET /api/paper/reconciliation` es exclusivamente read-only
- Suite fault-injection + smoke F88; bundle INTERNAL default F19–F88
- `LIVE_BLOCKED=True`; sin flip LIVE; sin `FASE_88_APPROVED.md`


## Fase 89 — A3 MD Read-only Certification

**Versión:** 0.81.0 · **DEC-133** · **APROBADO_INTERNO** (sin `FASE_89_APPROVED.md`)

- Lane fake-contract obligatoria CI/offline con spy/write-bomb
- Lane sandbox-env opt-in, exclusivamente simulation y sin fallback a fake
- Estados PASS/FAIL/SKIPPED_NOT_REQUESTED; skip no equivale a PASS
- Reporte frozen saneado: conteos/latencia/issues; sin secretos/account/raw
- Worker sandbox en subprocess con entorno allowlisted y timeout
- Sandbox real `SKIPPED_NOT_REQUESTED`: no se afirma certificación real
- Suite adversarial + smoke F89; bundle INTERNAL default F19–F89
- `LIVE_BLOCKED=True`; sin flip LIVE; sin `FASE_89_APPROVED.md`


## Fase 90 — Paper Reconciliation Status Panel

**Versión:** 0.82.0 · **DEC-134** · implementada, auditoría INTERNAL en curso

- Panel SPA `Reconciliación` read-only sobre `GET /api/paper/reconciliation`
- Badge ok/status, record_count, checkpoint (count/last_fill_id/sha256), issues
- Muestra `rebuild_via` (CLI offline F88); la UI no expone mutaciones HTTP
- Auto-refresh opcional 10 s con limpieza al cerrar
- Command palette `open.reconciliation` + menú Inicio + i18n es/en
- Suite UI wiring + read-only estricto + smoke F90; bundle default F19–F90
- `LIVE_BLOCKED=True`; sin flip LIVE; sin `FASE_90_APPROVED.md`


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

1. F0–F18 certificados externos; F19–F68 **APROBADO_INTERNO** (noche F19–F68; freeze v0.40 + v0.50 + v0.60).  
2. Certificados externos F19+ solo con APROBADO Meta-Auditor externo (no emitir desde INTERNAL).  
3. LIVE routing sigue **BLOQUEADO**; flip solo con checklist + Meta-Auditor + dueño.
