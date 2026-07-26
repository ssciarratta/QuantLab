# Changelog

Todos los cambios notables de QuantLab se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

---

## [Unreleased]

### Added
- TD-05: `FixedLatencyModel.min_delay` wall-clock con `bar_times` en `BarSimulationEngine`
- TD-03 research: federación de paper ledger (`node_id`, `reconcile_indexes`, `merge_from`)
- CI Actions versionado: `.github/workflows/ci.yml` (espejo `docs/ci/ci.yml.example`)

### Changed
- `.gitignore`: deja de excluir el workflow de CI
- `sync_phase_github.sh`: `SKIP_WORKFLOWS` default `0` (escape hatch `=1`)

---

## [0.61.0] — 2026-07-26

### Fase 69 — Risk Utilization Report

#### Added
- `GET /api/risk/utilization` — % used de `max_qty` / `max_notional` vs book/posiciones
- Helpers `compute_risk_utilization` / marks broker o avg (`workbench/risk_utilization.py`)
- Sección **Utilización** en panel Risk (peak qty + gross notional + breakdown)
- Docs: `FASE_69_RISK_UTIL.md` · implementation report · DEC-113
- Suite `test_risk_utilization_f69.py` + smoke F69
- Bundle INTERNAL default F19–F69

#### Changed
- `phases_summary` → `F19–F69 INTERNAL`
- Bump **0.61.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_69_APPROVED.md`

## [0.60.0] — 2026-07-26


### Fase 68 — Milestone Freeze Docs + CHANGELOG Sync (v0.60)

#### Added
- Freeze documental `docs/audit/MILESTONE_V060_FREEZE.md` (inventario F19–F67/F68)
- Smoke check: tip version **starts with 0.60**
- Docs: `FASE_68_MILESTONE_V060.md` · implementation report · DEC-112
- Bundle INTERNAL default F19–F68

#### Changed
- Sync tip: `CHANGELOG` · `RESUMEN_PROYECTO.txt` · `.cursor/PROJECT_MEMORY.md` · `README`
- `phases_summary` → `F19–F68 INTERNAL`
- Bump **0.60.0** (hito 0.60)

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_68_APPROVED.md`

### Resumen agrupado F19–F67 (producto previo al hito 0.60)

| Grupo | Fases | Versiones | Qué entrega |
|-------|-------|-----------|-------------|
| **Núcleo modos + UI** | F19–F22 | 0.11–0.14 | OperatingMode (REAL=PAPER); workbench loopback; lab panels; chat FakeProvider |
| **Paper + venues + ops** | F23–F25 | 0.15–0.17 | PaperBook/sesión/risk; plugins MD; Ops Desk 1-click + hardening |
| **Sesión + catálogo + layout** | F26–F28 | 0.18–0.20 | Paper Session Runner; Strategy Catalog MM/AS; layout + journal |
| **Lab research UI** | F29–F34 | 0.21–0.26 | Reports; universe/catalog; features; validation; optimizer; MC + HB export |
| **UX workbench** | F35–F40 | 0.27–0.32 | Command palette; settings/status; onboarding; docs help; session ZIP; presets |
| **Ops + hardening + E2E** | F41–F44 | 0.33–0.36 | Activity/toasts; ops metrics; red-team; E2E paper workflow |
| **Meta + polish** | F45–F48 | 0.37–0.40 | About/badge; multi-session; chat context; theme CSS |
| **Freeze v0.40 + ops prod** | F49–F54 | 0.41–0.46 | Milestone freeze v0.40; perf baseline; rate limit; shutdown; Docker; probes |
| **API surface + security** | F55–F57 | 0.47–0.49 | OpenAPI catalog; security headers; Content-Security-Policy |
| **Freeze v0.50 + a11y/i18n/ops** | F58–F64 | 0.50–0.56 | Milestone freeze v0.50; a11y; i18n es; access log + UI; auto-backup + UI |
| **Paper analytics** | F65–F67 | 0.57–0.59 | Blotter CSV export; equity curve; paper PnL summary |

Freeze: `docs/audit/MILESTONE_V060_FREEZE.md` · noche F19–F67 APROBADO_INTERNO · tip F68 **0.60.0** · **LIVE bloqueado**.

---

## [0.59.0] — 2026-07-26

### Fase 67 — Paper PnL Summary

#### Added
- `PaperBook.get_pnl` — realized/unrealized/equity/cash desde book + marks
- `GET /api/paper/pnl` — marks PaperBroker (mid/last) o avg fallback
- Headers PnL en Positions y Blotter
- Suite `tests/unit/workbench/test_paper_pnl_f67.py`
- Docs: `FASE_67_PNL.md` · implementation report · DEC-111
- Bundle INTERNAL default F19–F67

#### Changed
- `phases_summary` → `F19–F67 INTERNAL`
- Bump **0.59.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_67_APPROVED.md`

---

## [0.58.0] — 2026-07-26

### Fase 66 — Equity Curve Snapshot

#### Added
- Session `equity.jsonl` append-only (`ts`, `equity`, `cash`) en fills + paper session step
- `GET /api/paper/equity?limit=N` — últimos N puntos
- Sección Equity curve en Positions (lista + sparkline SVG)
- Suite `tests/unit/workbench/test_equity_curve_f66.py`
- Docs: `FASE_66_EQUITY.md` · implementation report · DEC-110
- Bundle INTERNAL default F19–F66

#### Changed
- `phases_summary` → `F19–F66 INTERNAL`
- Bump **0.58.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_66_APPROVED.md`

---

## [0.57.0] — 2026-07-26

### Fase 65 — Blotter CSV Server Export

#### Added
- `GET /api/paper/fills.csv` — `text/csv` de fills del journal paper (attachment)
- `PaperFillJournal.export_csv` / `fills_to_csv` — header estable + escape CSV
- Botón **Descargar CSV** en Blotter y Journal (`QLApi.paperFillsCsvUrl`)

- Suite `tests/unit/workbench/test_fills_csv_f65.py`
- Docs: `FASE_65_BLOTTER_CSV.md` · implementation report · DEC-109
- Bundle INTERNAL default F19–F65

#### Changed
- `phases_summary` → `F19–F65 INTERNAL`
- Bump **0.57.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_65_APPROVED.md`

---

## [0.56.0] — 2026-07-26

### Fase 64 — Backups Panel UI

#### Added
- Panel SPA Backups (`backups.js`) — lista `GET /api/backups` + botón **Backup ahora**
- `POST /api/backups/run` — trigger manual `run_auto_backup` + sidecar sha
- Menú Inicio → Sistema → Backups · command palette `open.backups`
- Suite `tests/unit/workbench/test_backups_ui_f64.py`
- Docs: `FASE_64_BACKUPS_UI.md` · implementation report · DEC-108
- Bundle INTERNAL default F19–F64

#### Changed
- `phases_summary` → `F19–F64 INTERNAL`
- Bump **0.56.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_64_APPROVED.md`

---

## [0.55.0] — 2026-07-26

### Fase 63 — Session Auto-Backup

#### Added
- `workbench/auto_backup.py` — `run_auto_backup` + scheduler daemon + rotación max 5
- Settings `auto_backup_minutes` (default **0=off**); si >0, ZIP periódico a `session/backups/`
- `GET /api/backups` — lista backups de la sesión activa
- Reusa allowlist + zip-slip fail-closed de `session_zip.export_session`
- Suite `tests/unit/workbench/test_auto_backup_f63.py`
- Docs: `FASE_63_AUTO_BACKUP.md` · implementation report · DEC-107
- Bundle INTERNAL default F19–F63

#### Changed
- `phases_summary` → `F19–F63 INTERNAL`
- Bump **0.55.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_63_APPROVED.md`

---

## [0.54.0] — 2026-07-26

### Fase 62 — Access Log Panel UI

#### Added
- Panel SPA Access Log (`static/js/panes/access_log.js`) · `QLApi.getAccessLog`
- Menú Inicio → Sistema → Access Log · command palette `open.access_log`
- Auto-refresh opcional (5s) + `dispose` al cerrar ventana (`wm.close`)
- i18n `pane.access_log` · CSS access-list
- Suite `tests/unit/workbench/test_access_log_ui_f62.py`
- Docs: `FASE_62_ACCESS_LOG_UI.md` · implementation report · DEC-106
- Bundle INTERNAL default F19–F62

#### Changed
- `phases_summary` → `F19–F62 INTERNAL`
- Bump **0.54.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_62_APPROVED.md`

---

## [0.53.0] — 2026-07-26

### Fase 61 — Workbench Request Access Log

#### Added
- `workbench/access_log.py` — `AccessLog` JSONL append-only (method, path, status, ms)
- Session `access.jsonl` (+ ZIP export F39)
- Settings `access_log: true` (default) · checkbox UI
- Middleware server `_begin_access` / `_finish_access`
- `GET /api/access-log?limit=100` · OpenAPI catalog
- Suite `tests/unit/workbench/test_access_log_f61.py`
- Docs: `FASE_61_ACCESS_LOG.md` · implementation report · DEC-105
- Bundle INTERNAL default F19–F61

#### Changed
- `phases_summary` → `F19–F61 INTERNAL`
- Bump **0.53.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_61_APPROVED.md`; sin bodies/secrets en el log

---

## [0.52.0] — 2026-07-26

### Fase 60 — i18n Scaffold (es default)

#### Added
- `static/js/i18n.js` — `QLi18n` (es + stub en) · `t()` · `applyDom`
- `static/i18n/es.json` · `en.json`
- `GET /api/i18n/{locale}` (Python loader desde static JSON)
- Shell aplica `settings.locale` al load; `data-i18n` en menú / chrome
- Settings locale `es|en` (default es)
- Suite `tests/unit/workbench/test_i18n_f60.py`
- Docs: `FASE_60_I18N.md` · implementation report · DEC-104
- Bundle INTERNAL default F19–F60

#### Changed
- `phases_summary` → `F19–F60 INTERNAL`
- Bump **0.52.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_60_APPROVED.md`

---

## [0.51.0] — 2026-07-26

### Fase 59 — A11y Basics (focus + aria)

#### Added
- Skip link «Ir al contenido» → `#workspace`
- Dialog shells `role="dialog"` + `aria-modal` (palette / about / onboarding) en `index.html`
- Focus trap básico (Tab ciclo) en Command Palette
- `aria-label` en botones taskbar (inicio + ventanas)
- Suite `tests/unit/workbench/test_a11y_f59.py`
- Docs: `FASE_59_A11Y.md` · implementation report · DEC-103
- Bundle INTERNAL default F19–F59

#### Changed
- `phases_summary` → `F19–F59 INTERNAL`
- Bump **0.51.0**

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_59_APPROVED.md`

---

## [0.50.0] — 2026-07-26

### Fase 58 — Milestone Freeze Docs + CHANGELOG Sync (v0.50)

#### Added
- Freeze documental `docs/audit/MILESTONE_V050_FREEZE.md` (inventario F19–F57/F58)
- Smoke check: tip version **starts with 0.50**
- Docs: `FASE_58_MILESTONE_V050.md` · implementation report · DEC-102
- Bundle INTERNAL default F19–F58

#### Changed
- Sync tip: `CHANGELOG` · `RESUMEN_PROYECTO.txt` · `.cursor/PROJECT_MEMORY.md` · `README`
- `phases_summary` → `F19–F58 INTERNAL`
- Bump **0.50.0** (hito 0.50)

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_58_APPROVED.md`

### Resumen agrupado F19–F57 (producto previo al hito 0.50)

| Grupo | Fases | Versiones | Qué entrega |
|-------|-------|-----------|-------------|
| **Núcleo modos + UI** | F19–F22 | 0.11–0.14 | OperatingMode (REAL=PAPER); workbench loopback; lab panels; chat FakeProvider |
| **Paper + venues + ops** | F23–F25 | 0.15–0.17 | PaperBook/sesión/risk; plugins MD; Ops Desk 1-click + hardening |
| **Sesión + catálogo + layout** | F26–F28 | 0.18–0.20 | Paper Session Runner; Strategy Catalog MM/AS; layout + journal |
| **Lab research UI** | F29–F34 | 0.21–0.26 | Reports; universe/catalog; features; validation; optimizer; MC + HB export |
| **UX workbench** | F35–F40 | 0.27–0.32 | Command palette; settings/status; onboarding; docs help; session ZIP; presets |
| **Ops + hardening + E2E** | F41–F44 | 0.33–0.36 | Activity/toasts; ops metrics; red-team; E2E paper workflow |
| **Meta + polish** | F45–F48 | 0.37–0.40 | About/badge; multi-session; chat context; theme CSS |
| **Freeze v0.40 + ops prod** | F49–F54 | 0.41–0.46 | Milestone freeze v0.40; perf baseline; rate limit; shutdown; Docker; probes |
| **API surface + security** | F55–F57 | 0.47–0.49 | OpenAPI catalog; security headers; Content-Security-Policy |

Freeze: `docs/audit/MILESTONE_V050_FREEZE.md` · noche F19–F57 APROBADO_INTERNO · tip F58 **0.50.0** · **LIVE bloqueado**.

---

## [0.49.0] — 2026-07-26

### Fase 57 — Content-Security-Policy

#### Added
- Header `Content-Security-Policy` en respuestas workbench (SPA local)
- Política: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'`
- Suite `tests/unit/workbench/test_csp_f57.py`
- Docs: `FASE_57_CSP.md` · implementation report · DEC-101
- Bundle INTERNAL default F19–F57

#### Changed
- `phases_summary` → `F19–F57 INTERNAL`
- `security_headers.SECURITY_HEADERS` incluye CSP (F56 headers intactos)

#### Security
- Sin `unsafe-eval`; scripts solo externos `/static/js/*`
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_57_APPROVED.md`

---

## [0.48.0] — 2026-07-26

### Fase 56 — Security Headers

#### Added
- Headers workbench: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`
- `Cache-Control: no-store` en `/api/*`
- Módulo `quantlab.workbench.security_headers` (CORS fail-closed)
- Suite `tests/unit/workbench/test_security_headers_f56.py`
- Docs: `FASE_56_SECURITY_HEADERS.md` · implementation report · DEC-100
- Bundle INTERNAL default F19–F56

#### Changed
- `phases_summary` → `F19–F56 INTERNAL`

#### Security
- Nunca `Access-Control-Allow-Origin: *`; Origin non-loopback no se refleja
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_56_APPROVED.md`

---

## [0.47.0] — 2026-07-26

### Fase 55 — OpenAPI / API Catalog

#### Added
- `GET /api/openapi.json` — OpenAPI 3 mínimo desde catálogo estático
- Módulo `quantlab.workbench.api_catalog` (paths/methods/summary; sin FastAPI)
- Link About → API (OpenAPI)
- Suite `tests/unit/workbench/test_openapi_f55.py`
- Docs: `FASE_55_OPENAPI.md` · implementation report · DEC-099
- Bundle INTERNAL default F19–F55

#### Changed
- `phases_summary` → `F19–F55 INTERNAL`

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_55_APPROVED.md`; sin rutas LIVE trading en catálogo

---

## [0.46.0] — 2026-07-26

### Fase 54 — Readiness / Liveness Probes

#### Added
- `GET /api/livez` — liveness (siempre 200 si proceso up)
- `GET /api/readyz` — readiness (200 si `LIVE_BLOCKED` + session root writable; 503 si no)
- Módulo `quantlab.workbench.probes`
- Ops: `DOCKER_WORKBENCH.md` documenta HEALTHCHECK con probes
- Suite `tests/unit/workbench/test_probes_f54.py`
- Docs: `FASE_54_PROBES.md` · implementation report · DEC-098
- Bundle INTERNAL default F19–F54

#### Changed
- `phases_summary` → `F19–F54 INTERNAL`

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_54_APPROVED.md`

---

## [0.45.0] — 2026-07-26

### Fase 53 — Dockerfile Workbench (opt-in)

#### Added
- `Dockerfile.workbench` — python 3.12-slim + `uv sync` · EXPOSE 8765
- CMD `quantlab-workbench --host 0.0.0.0 --allow-non-loopback --no-browser`
  (riesgo documentado; solo Docker Desktop port-map)
- `.dockerignore` (sin `.env` / data secrets)
- Ops: `docs/ops/DOCKER_WORKBENCH.md` (`-p 127.0.0.1:8765:8765`)
- Suite `tests/unit/workbench/test_dockerfile_f53.py` (parse file; sin build obligatorio)
- Docs: `FASE_53_DOCKER.md` · implementation report · DEC-097
- Bundle INTERNAL default F19–F53

#### Changed
- `phases_summary` → `F19–F53 INTERNAL`

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_53_APPROVED.md`
- Publish recomendado solo loopback host; sin auth HTTP

---

## [0.44.0] — 2026-07-26

### Fase 52 — Graceful Shutdown + Paper Session Safety

#### Added
- `quantlab.workbench.shutdown` — stop paper + flush layout/settings/book
- SIGINT/SIGTERM handlers en `launch.py` → graceful shutdown
- `POST /api/shutdown` loopback-only (tests/automatización)
- Suite `tests/unit/workbench/test_shutdown_f52.py`
- Docs: `FASE_52_SHUTDOWN.md` · implementation report · DEC-096
- Bundle INTERNAL default F19–F52

#### Changed
- `phases_summary` → `F19–F52 INTERNAL`

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_52_APPROVED.md`

---

## [0.43.0] — 2026-07-26

### Fase 51 — API Rate Limit (loopback soft)

#### Added
- `quantlab.workbench.rate_limit` — token bucket in-process por IP/path
- Soft limit en `server.py` (GET/POST/PUT) → 429 JSON + `Retry-After`
- Default 120 req/s · burst 120; inyección `configure_rate_limit`
- Suite `tests/unit/workbench/test_rate_limit_f51.py`
- Docs: `FASE_51_RATE_LIMIT.md` · implementation report · DEC-095
- Bundle INTERNAL default F19–F51

#### Changed
- `phases_summary` → `F19–F51 INTERNAL`

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_51_APPROVED.md`

---

## [0.42.0] — 2026-07-26

### Fase 50 — Performance Baseline Workbench API

#### Added
- `quantlab.workbench.perf_baseline` — medición p50/p95/max de endpoints clave
- Suite `tests/unit/workbench/test_perf_baseline_f50.py` (assert p95/max < 500ms)
- CLI `scripts/workbench_perf_baseline.py`
- Docs: `FASE_50_PERF_BASELINE.md` · implementation report · DEC-094
- Bundle INTERNAL default F19–F50

#### Changed
- `phases_summary` → `F19–F50 INTERNAL`

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_50_APPROVED.md`

---

## [0.41.0] — 2026-07-26

### Fase 49 — Milestone Freeze Docs + CHANGELOG Sync

#### Added
- Freeze documental `docs/audit/MILESTONE_V040_FREEZE.md` (inventario F19–F48)
- Smoke check: About / health `version` ≡ `quantlab.__version__`
- Docs: `FASE_49_MILESTONE.md` · implementation report · DEC-093
- Bundle INTERNAL default F19–F49

#### Changed
- Sync tip: `CHANGELOG` · `RESUMEN_PROYECTO.txt` · `.cursor/PROJECT_MEMORY.md` · `README`
- `phases_summary` → `F19–F49 INTERNAL`

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin `FASE_49_APPROVED.md`

### Resumen agrupado F19–F48 (milestone v0.40.0)

| Grupo | Fases | Versiones | Qué entrega |
|-------|-------|-----------|-------------|
| **Núcleo modos + UI** | F19–F22 | 0.11–0.14 | OperatingMode (REAL=PAPER); workbench loopback; lab panels; chat FakeProvider |
| **Paper + venues + ops** | F23–F25 | 0.15–0.17 | PaperBook/sesión/risk; plugins MD; Ops Desk 1-click + hardening |
| **Sesión + catálogo + layout** | F26–F28 | 0.18–0.20 | Paper Session Runner; Strategy Catalog MM/AS; layout + journal |
| **Lab research UI** | F29–F34 | 0.21–0.26 | Reports; universe/catalog; features; validation; optimizer; MC + HB export |
| **UX workbench** | F35–F40 | 0.27–0.32 | Command palette; settings/status; onboarding; docs help; session ZIP; presets |
| **Ops + hardening + E2E** | F41–F44 | 0.33–0.36 | Activity/toasts; ops metrics; red-team; E2E paper workflow |
| **Meta + polish** | F45–F48 | 0.37–0.40 | About/badge; multi-session; chat context; theme CSS slate/high-contrast |

Freeze: `docs/audit/MILESTONE_V040_FREEZE.md` · noche F19–F48 APROBADO_INTERNO · **LIVE bloqueado**.

---

## [0.40.0] — 2026-07-26

### Fase 48 — Theme CSS Completion (slate + high-contrast)

#### Added
- Tokens CSS completos para themes `slate` | `high-contrast` (chrome + semantic)
- `data-theme` en `documentElement` (+ body) al load settings y PUT `/api/settings`
- Docs: `FASE_48_THEMES.md` · implementation report · DEC-092

#### Security
- `LIVE_BLOCKED is True` (sin flip)

---

## [0.39.0] — 2026-07-26

### Fase 47 — Chat Context Awareness

#### Added
- Chat tools allowlist: `get_session_summary`, `list_reports`, `list_strategies` (read-only)
- FakeProvider intents ES: «cómo estoy», «resumen sesión», «qué reportes hay», «estrategias»
- Docs: `FASE_47_CHAT_CONTEXT.md` · implementation report · DEC-091

#### Security
- `LIVE_BLOCKED is True` (sin flip); chat sin trading tools; ilegal tools rechazados

---

## [0.38.0] — 2026-07-26

### Fase 46 — Multi-Session Switcher

#### Added
- API `GET /api/sessions` + `POST /api/sessions/switch` + `POST /api/sessions/new`
- UI panel Sessions (menú Inicio / `open.sessions`)
- Docs: `FASE_46_SESSIONS.md` · implementation report · DEC-090

#### Security
- `LIVE_BLOCKED is True` (sin flip); `validate_session_id` fail-closed en switch

---

## [0.37.0] — 2026-07-26

### Fase 45 — About Dialog + Version Badge

#### Added
- API `GET /api/about` (version, live_blocked, phases_summary, python, bind_policy)
- Badge versión en status bar + diálogo Acerca de (menú Inicio / `open.about`)
- Docs: `FASE_45_ABOUT.md` · implementation report · DEC-089

#### Security
- `LIVE_BLOCKED is True` (sin flip); superficie read-only

---

## [0.36.0] — 2026-07-26

### Fase 44 — E2E Paper Workflow Integration Test

#### Added
- Test integración `test_e2e_paper_workflow_f44.py` (API loopback, sin browser)
- Flujo: mode paper → connect binance/a3 tester → submit → positions/book →
  paper session buy_once+step → backtest+reports → validation+optimize+mc →
  export HB → session zip → LIVE reject
- Docs: `FASE_44_E2E_WORKFLOW.md` · implementation report · DEC-088

#### Security
- `LIVE_BLOCKED is True` (sin flip); modo live rechazado al cierre del flujo

---

## [0.35.0] — 2026-07-26

### Fase 43 — Red-team Workbench Hardening

#### Added
- Tests red-team `test_redteam_f43.py` (path traversal, LIVE, host, body)
- Docs: `FASE_43_REDTEAM.md` · implementation report · DEC-087

#### Security
- `zip_path` sandbox bajo session parent (`allowed_roots`)
- `create_server` fail-closed: non-loopback requiere `allow_non_loopback`
- Body JSON default **2 MiB**; segmentos URL anti-`..`
- `csv_path` anti-traversal en broker connect
- `LIVE_BLOCKED is True` (sin flip)

---

## [0.32.0] — 2026-07-26

### Fase 40 — Workspace Presets

#### Added
- `workbench/presets.py` — presets `research` / `trading_paper` / `ops`
- API `GET /api/presets` + `POST /api/presets/apply`
- Menú Inicio → Espacios de trabajo (aplica layout.json)
- Tests `test_presets_f40.py` · DEC-084
- Docs: `FASE_40_PRESETS.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); nombre de preset fail-closed; sin place_order venue

---

## [0.31.0] — 2026-07-26

### Fase 39 — Session Export/Import ZIP

#### Added
- `workbench/session_zip.py` — export/import ZIP sin secretos + zip-slip fail-closed
- API `GET /api/session/export` (+ `?download=1`) + `POST /api/session/import`
- UI Export/Import en panel Settings
- Tests `test_session_zip_f39.py` · DEC-083
- Docs: `FASE_39_SESSION_ZIP.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); secretos denylist; zip-slip fail-closed

---

## [0.30.0] — 2026-07-26

### Fase 38 — Docs / Help Browser

#### Added
- `workbench/docs_browser.py` — lista/lee `docs/*.md` + `docs/ops/*.md` fail-closed
- API `GET /api/docs` + `GET /api/docs/content?path=`
- Panel Help/Docs (buscar + preview HTML escapado | pre text)
- Chat `search_docs` incluye ops/; command palette `open.docs`
- Tests `test_docs_f38.py` · DEC-082
- Docs: `FASE_38_DOCS_HELP.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); path traversal fail-closed; sin place_order venue

---

## [0.29.0] — 2026-07-26

### Fase 37 — First-run Onboarding Wizard

#### Added
- `workbench/onboarding.py` — flag `onboarding_done` en session `meta.json`
- API `GET /api/onboarding` + `POST /api/onboarding/complete`
- Wizard modal 4 pasos (modos · venue tester · Paper/Backtest · Chat IA safe)
- Tests `test_onboarding_f37.py` · DEC-081
- Docs: `FASE_37_ONBOARDING.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); wizard explica LIVE bloqueado; sin place_order venue

---

## [0.28.0] — 2026-07-26

### Fase 36 — Settings + Status Bar

#### Added
- `workbench/settings.py` — `settings.json` por sesión (theme, venue, strategy, slip, locale es)
- API `GET/PUT /api/settings` (LIVE_BLOCKED, research_safe, sin LIVE)
- Panel Settings UI + status bar fija (mode, live, session, venue, md, clock)
- Themes CSS `slate` | `high-contrast`
- Tests `test_settings_f36.py` · DEC-080
- Docs: `FASE_36_SETTINGS.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); settings fail-closed (theme/locale/strategy/slip)

---

## [0.27.0] — 2026-07-26

### Fase 35 — Command Palette + Keyboard Shortcuts

#### Added
- `workbench/commands.py` — registry paneles + acciones seguras
- API `GET /api/commands` (LIVE_BLOCKED, research_safe, sin LIVE)
- Command palette JS (`Ctrl+K` / `Ctrl+Shift+P`) · atajos `Ctrl+1..9`, `Esc`, `Ctrl+W`
- Tests `test_commands_f35.py` · DEC-079
- Docs: `FASE_35_COMMAND_PALETTE.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); comandos solo safe (health refresh / open pane / close)

---

## [0.26.0] — 2026-07-26

### Fase 34 — Monte Carlo History + Hummingbot Export Wizard

#### Added
- `workbench/montecarlo_runs.py` — persist session `montecarlo/<run_id>/summary.json`
- API `GET /api/lab/montecarlo/history` (+ `/{run_id}`) · POST `/api/lab/montecarlo` enriquecido (CI)
- `workbench/hb_exports.py` · `GET /api/lab/exports` (+ `/{id}`) · export wizard steps
- Panel MC (historial + intervalos) · panel Export HB (experiments + banner live_routing:false)
- Tests `test_mc_export_f34.py` · DEC-078
- Docs: `FASE_34_MC_EXPORT.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); path externo MC/export rechazado; export siempre `live_routing:false`

---

## [0.25.0] — 2026-07-26

### Fase 33 — Optimizer History + Pareto Panel

#### Added
- `workbench/optimizer_runs.py` — persist session `optimizer/<run_id>/summary.json`
- API `GET /api/lab/optimize/history` (+ `/{run_id}`) · POST `/api/lab/optimize` enriquecido
- Pareto multi-objetivo simple (sharpe↑ / MDD↓) + panel Optimizer (tabla + SVG)
- Tests `test_optimizer_f33.py` · DEC-077
- Docs: `FASE_33_OPTIMIZER_UI.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); path externo de optimizer rechazado

---

## [0.24.0] — 2026-07-26

### Fase 32 — Validation / Walk-Forward Runner UI

#### Added
- `workbench/validation_runs.py` — persist session `validation/<run_id>/summary.json`
- API `POST /api/lab/validation/run` · `GET /api/lab/validation` (+ `/{run_id}`)
- Índices de segmentos + anti-leakage (`check_temporal_leakage`); panel Validation enriquecido
- Tests `test_validation_f32.py` · DEC-076
- Docs: `FASE_32_VALIDATION_UI.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); path externo de validation rechazado

---

## [0.23.0] — 2026-07-26

### Fase 31 — Feature Store Browser + Pipeline Runner UI

#### Added
- `workbench/feature_store_browser.py` — list read-only FeatureStore (session/features)
- API `GET /api/lab/features/store`, `POST /api/lab/features/run` (alias `/api/lab/features`)
- Persist demo via `FeatureStore.put` en sesión; panel Features (store + columnas)
- Tests `test_features_store_f31.py` · DEC-075
- Docs: `FASE_31_FEATURES_UI.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); path externo de store rechazado; store list read-only

---

## [0.22.0] — 2026-07-26

### Fase 30 — Universe Watchlist + Data Catalog Browser

#### Added
- `workbench/watchlist.py` — `watchlist.json` por sesión (add/remove)
- `workbench/catalog_browser.py` — list read-only vía `quantlab.data.catalog`
- API `GET`/`PUT` `/api/watchlist`, `GET /api/universe`, `GET /api/catalog`
- Paneles UI Universe + Catalog; click símbolo → Market/Session
- Tests `test_universe_catalog_f30.py` · DEC-074
- Docs: `FASE_30_UNIVERSE_CATALOG.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); symbol charset fail-closed; catalog no crea DB si falta

---

## [0.21.0] — 2026-07-26

### Fase 29 — Report Viewer + Metrics History

#### Added
- `workbench/reports.py` — persist MetricsResult/summary (+ HTML ReportGenerator) en session `reports/`
- API `GET /api/lab/reports`, `GET /api/lab/reports/{id}` (POST implícito en backtest)
- Panel UI Reports: lista + preview HTML|JSON
- Tests `test_reports_f29.py` · DEC-073
- Docs: `FASE_29_REPORTS.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); report_id fail-closed (charset / sandbox)

---

## [0.20.0] — 2026-07-26

### Fase 28 — Workbench Layout Persistence + Journal Viewer

#### Added
- `workbench/layout.py` — save/load `layout.json` por sesión (geometría MDI)
- API `GET`/`PUT` `/api/layout`
- `wm.js` debounce save en move/resize + restore al boot
- Panel Journal (`panes/journal.js`): tabla fills + export CSV client-side
- Tests `test_layout_f28.py` · DEC-072
- Docs: `FASE_28_LAYOUT_JOURNAL.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); layout fail-closed (ids/rangos)

---

## [0.19.0] — 2026-07-26

### Fase 27 — Strategy Catalog (workbench)

#### Added
- Catálogo compartido `workbench/strategy_catalog.py` (dummy, buy_once, momentum, inventory_mm, avellaneda_stoikov)
- Wire `InventoryMMStrategy` + `AvellanedaStoikovStrategy` en paper session + lab backtest
- `GET /api/lab/strategies` + `strategy_catalog` en capabilities
- UI selectores + params básicos (Sesión Paper / Backtest)
- Adapter bar-based para MM en lab (`BarSyntheticBookAdapter`)
- Tests smoke por `strategy_id` · DEC-071
- Docs: `FASE_27_STRATEGY_CATALOG.md` · implementation report

#### Security
- `LIVE_BLOCKED is True` (sin flip); sin place_order venue

---

## [0.18.0] — 2026-07-26

### Fase 26 — Paper Session Runner

#### Added
- `PaperSessionRunner` / `PaperSessionConfig` (`workbench/paper_session.py`)
- API `/api/paper/session/{start,stop,step,status}`
- UI panel «Sesión Paper» (Inicio → Sesión Paper)
- Background opcional `interval_ms` (daemon cancelable)
- Tests `test_paper_session_runner.py`

#### Security
- `LIVE_BLOCKED is True` (sin flip); nunca place_order venue
- Audit INTERNAL: constructor fail-closed solo `PaperBroker` (H1); DEC-070
- Docs: `AUTO_AUDIT_2026-07-26_F26` · `INTERNAL_AUDIT_F26` · noche F19–F26
- `FASE_26_APPROVED.md` **no** emitido (reserva Meta-Auditor externo)

---

## [0.17.0] — 2026-07-26

### Fase 25 — Ops Desk (1-click + hardening)

#### Added
- `scripts/launch_workbench.sh` + `packaging/quantlab-workbench.desktop` + `docs/ops/WORKBENCH_1CLICK.md`
- CLI `--allow-non-loopback` / `--slippage-bps`; `GET /api/risk`; panel Riesgo
- PaperBroker `slippage_bps` adverso (buy/sell worse)
- `validate_experiment_id` charset `^[A-Za-z0-9_-]+$`
- Tests non-loopback, experiment_id, paper slippage; smoke F23/F24/F25

#### Security
- Host no-loopback abort exit 2 sin flag; warning si se permite
- `LIVE_BLOCKED is True` (sin flip)

#### Docs / audit (post-impl)
- INTERNAL APROBADO_INTERNO F25 + arco F23–F25 + noche F19–F25
- DEC-069; tests API risk + allow-non-loopback warning; smoke 11 checks

---

## [0.16.0] — 2026-07-26

### Fase 24 — Venue plugins + MD read-only multiplataforma

#### Added
- Entry points `quantlab.brokers` (`brokers/plugins.py`); `get_default_registry` carga plugins
- A3 `md_source` fake|env (`QUANTLAB_A3_MD_READONLY=1` + creds; fallback fake)
- Builtins `generic_csv` / `generic_rest` (MD-only skeletons)
- Workbench: connect `md_source`; health/session `md_provider` / `plugin_venues`; UI Market provider
- Docs: `docs/ops/BROKER_PLUGINS.md`; DEC-067/068

#### Security
- submit/cancel en A3 + generics → `assert_live_routing_blocked`
- `LIVE_BLOCKED is True` (sin flip)

---

## [0.15.0] — 2026-07-26

### Fase 23 — Paper Book + Session durable + Risk paper

#### Added
- `PaperBook`: posiciones, cash, avg ponderado, equity MTM; `to_dict`/`from_dict`
- `PaperBroker` actualiza book en PLACE; `get_positions`/`get_account` desde book
- `WorkbenchSession` durable bajo `data/runtime/workbench/<id>/`
- `PaperRiskLimits` fail-closed en paper submit (max qty/notional/symbols)
- API: `GET /api/broker/positions`, `GET /api/paper/book`, `GET /api/session`
- UI panel Posiciones + banner `session_id` + equity en blotter
- CLI: `--session-id`, `--session-root`, `--initial-cash`

#### Security
- Short rechazado por defecto (`allow_short=False`)
- `LIVE_BLOCKED is True` (sin flip)

---

## [0.14.0] — 2026-07-26

### Fase 22 — Chat IA safe-by-default (APROBADO_INTERNO)

#### Added
- `workbench/chat/`: ToolRegistry allowlist, FakeProvider, OptionalEnvProvider, ChatAuditLog, ChatOrchestrator
- API `POST /api/chat` + `GET /api/chat/tools`; panel Chat IA + banner safe-mode
- Tests `tests/unit/workbench/test_chat_*.py` (17)
- Smoke `scripts/internal_audit_smoke.py` (LIVE + imports workbench/brokers/chat)
- Auditoría INTERNAL F22 + cierre arco F19–F22

#### Security
- Illegal tools rechazados; chat no puede `set_live` / `place_order` / `submit_order`
- `LIVE_BLOCKED is True`; FakeProvider default CI; `QUANTLAB_LLM_*=DISABLED` en `.env.example`

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
