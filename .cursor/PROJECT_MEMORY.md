# QuantLab — PROJECT MEMORY (Cursor)

**Actualizado:** 2026-07-31  
**Branch trabajo:** `cursor/modo-real-workbench-aafd`  
**Versión tip:** **1.01.0** · Chat IA mentor (mapa + MC/Sim/Scanner)  
**Simulador:** comparar · ranking · **sin monedas default** · búsqueda on-demand · botón **MC con esta selección** · memo · registro  
**Monte Carlo:** estrés N escenarios · **ligado de verdad al Sim** (confirm + velas reales + strategy_id) · mode=`sim_linked` · memo CONTEXTO ORIGEN  
**Lección:** banner/memo cosmético ≠ motor; `sim_context` debe ir en el POST y usarse en `run_lab_montecarlo`  
**Registro UI:** ventana WM `sim_registry` · **Reabrir** restaura params · Memo · localStorage  
**Estrategias:** panel propio · «Abrir en Simulador»  
**Menú QL:** favoritos **Mis simulaciones → Chat IA → Scanner → Simulador → Estrategias** · Reabrir trae panel al frente  
**Alpha Scanner:** multi-mercado · **Moneda puntual = typeahead catálogo** · preview `≈ N velas · período × TF`  
**Chat IA:** system prompt mapa paneles · tools `explain_*` · open simulator/MC/strategies/sim_registry · chips UI · FakeProvider entiende «monte carlo»  
**Números UI:** `QLFmt` 2 decimales  
**Roles:** Guided=aprender · Sim=comparar · Scanner=ranking · MC=estrés (no predicción)  
**Monte Carlo corrección:** N hasta 1e6 · batching/jobs · DatasetReference · anti-huérfano · “velas por escenario” · schema v1 legible · ver `docs/progress/montecarlo-correction-status.md`  
**Deep-link:** `static/js/nav.js` + `QLShell.open(pane, opts)` · Reports/Backtest/Guided Lab → MC · MC → Reports/Guided Lab por id  
**Manuales:** `docs/manuales/` (índice + 35 paneles) · Help allowlist `ops|manuales|montecarlo|scanner` · entrada `docs/MANUALES.md` · GUIA_COMPLETA actualizada  
**Pendiente UX:** Guided Lab sigue scroll (intro aclara vs Simulador); params editables a mano por estrategia en Comparar  
**Singleton + update banner:** al abrir mata Workbench previo (PID/puerto) · banner v local + GH tip + sync · «mod» = max(commit, GH, mtime working tree `src/quantlab`) · `/api/update/*`  
**Pendiente UX:** Guided Lab rediseño cascada/solapas (solo diseño previo)  
  
**Milestone congelado arco v0.80:** F79–F91 · `docs/audit/MILESTONE_V080_ARC_FREEZE.md`  
**Milestone congelado arco ops v0.90:** F93–F97 · `docs/audit/MILESTONE_V090_OPS_ARC_FREEZE.md`  
**Milestone congelado arco LIVE v0.95:** F99–F102 · `docs/audit/MILESTONE_V095_LIVE_ARC_FREEZE.md`  
**Milestone congelado v0.40:** F19–F48 · `docs/audit/MILESTONE_V040_FREEZE.md`  
**Milestone congelado v0.50:** F19–F57/F58 · `docs/audit/MILESTONE_V050_FREEZE.md`  
**Milestone congelado v0.60:** F19–F67/F68 · `docs/audit/MILESTONE_V060_FREEZE.md`  
**Milestone congelado v0.70:** F19–F77/F78 · `docs/audit/MILESTONE_V070_FREEZE.md`  
**Milestone congelado arco Guided v1.00:** F99–F109 · `docs/audit/MILESTONE_V100_GUIDED_ARC_FREEZE.md`  

---

## Identidad

QuantLab = laboratorio de investigación cuantitativa (no bot de trading).  
Ejecución live / order routing venue = **bloqueado por diseño**.

---

## Estado de fases (resumen)

| Rango | Estado |
|-------|--------|
| F0–F18 | Certificados **externos** (`FASE_*_APPROVED.md`) |
| F19–F48 | **APROBADO_INTERNO** Zero-Trust; milestone v0.40.0 freeze |
| F49–F57 | Ops / API / security · **0.41–0.49** |
| F58 | Milestone freeze docs + CHANGELOG sync (v0.50) · **0.50.0** |
| F59–F67 | A11y / i18n / access / backups / paper analytics · **0.51–0.59** |
| F68 | Milestone freeze docs + CHANGELOG sync (v0.60) · **0.60.0** |
| F69–F77 | Risk / kill / health / alerts / clock / broker ops · **0.61–0.69** |
| F78 | Milestone freeze docs + CHANGELOG sync (v0.70) · **0.70.0** |
| F79 | Watchlist import/export JSON · **0.71.0** |
| F80 | Custom preset save · **0.72.0** |
| F81 | Custom preset delete · **0.73.0** |
| F82 | Window snap to edges · **0.74.0** |
| F83 | Minimize / Restore All · **0.75.0** |
| F84 | Cascade / Tile Windows · **0.76.0** |
| F85 | Bring to Front / Send to Back · **0.77.0** |
| F86 | Maximize / Restore Window · **0.78.0** |
| F87 | Broker Plugin Contract v1 · **0.79.0** |
| F88 | Paper Journal authoritative + reconciliation · **0.80.0** |
| Arco F19–F22 | `docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md` |
| Arco F23–F25 | `docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md` |
| F89 | A3 MD certification harness · **0.81.0** |
| F90 | Paper Reconciliation Status Panel · **0.82.0** |
| F91 | Paper Session Rehydrate post-rebuild · **0.83.0** |
| F92 | Milestone Freeze Docs arco v0.71–v0.83 · **0.84.0** |
| F93 | Venues / Broker Registry Panel read-only · **0.85.0** |
| F94 | API Explorer Panel read-only · **0.86.0** |
| F95 | Diagnostics Snapshot Panel read-only · **0.87.0** |
| F96 | Diagnostics Download support snapshot · **0.88.0** |
| F97 | Support Bundle ZIP · **0.89.0** |
| F98 | Milestone freeze arco ops v0.90 · **0.90.0** |
| F99 | Guided Lab MVP wizard paper · **0.91.0** |
| F100 | LIVE credential gate + Binance public MD · **0.92.0** |
| F101 | Binance demo routing post-unlock · **0.93.0** |
| F102 | Binance Spot Testnet opt-in · **0.94.0** |
| F103 | Freeze arco LIVE Guided Path F99–F102 · **0.95.0** |
| F104 | Guided Lab A3 paper/MD · **0.96.0** |
| F105 | A3 MD env Guided Lab · **0.97.0** |
| F106 | Guided Lab A3 snapshot MD · **0.98.0** |
| F107 | Guided Lab A3 paper submit · **0.99.0** |
| F108 | Guided Lab i18n + venue-aware UX · **1.00.0** |
| F109 | LIVE demo cancel/LIMIT/mirror · **1.00.0** |
| F110 | Milestone freeze arco Guided F99–F109 · **1.00.0** |
| F111 | Binance alpha klines + pipeline + chat copilot · **1.01.0** |
| F112+ | Chat instructor/memoria/LLM + UI font/resize/tips (tip interno, sin freeze) |
| F115 | Espectro estrategias: 50 ids · 39 runnable · 11 stubs · tip interno |
| Noche F19–F96 | `docs/audit/INTERNAL_AUDIT_F19_F96_NIGHT.md` |

**Regla:** el auditor INTERNAL **no** emite `FASE_*_APPROVED.md` (reserva Meta-Auditor externo).

---

## Arco nocturno F19–F87 (SHAs impl) — tip v0.79.0

| Fase | Tema | Ver | Impl |
|------|------|-----|------|
| 19 | OperatingMode + BrokerPort; REAL=PAPER | 0.11.0 | `a5b12d3` |
| 20 | Workbench stdlib loopback + SPA WM | 0.12.0 | `cacf8e6` |
| 21 | Lab panels `/api/lab/*` | 0.13.0 | `c397ffc` |
| 22 | Chat IA allowlist + FakeProvider | 0.14.0 | `5ef9866` |
| 23 | PaperBook + sesión + risk | 0.15.0 | `9b89274` |
| 24 | Venue plugins + MD read-only | 0.16.0 | `c846e81` |
| 25 | Ops Desk 1-click + hardening | 0.17.0 | `21fe144` |
| 26 | Paper Session Runner | 0.18.0 | `46487a4` |
| 27 | Strategy Catalog (MM + AS) | 0.19.0 | `244a3fb` |
| 28 | Layout persistence + Journal | 0.20.0 | `86517cf` |
| 29 | Report Viewer + Metrics History | 0.21.0 | `2f37bf7` |
| 30 | Universe Watchlist + Data Catalog | 0.22.0 | `7d8bf88` |
| 31 | Feature Store Browser + Pipeline | 0.23.0 | `70a8ee2` |
| 32 | Validation / Walk-Forward Runner UI | 0.24.0 | `8c1cf58` |
| 33 | Optimizer History + Pareto Panel | 0.25.0 | `c39a57f` |
| 34 | Monte Carlo History + HB Export | 0.26.0 | `18cea7c` |
| 35 | Command Palette + Keyboard Shortcuts | 0.27.0 | `314b2cd` |
| 36 | Settings + Status Bar | 0.28.0 | `2c0cb11` |
| 37 | First-run Onboarding Wizard | 0.29.0 | `81ff9b1` |
| 38 | Docs / Help Browser | 0.30.0 | `becd116` |
| 39 | Session Export/Import ZIP | 0.31.0 | `0cb9d7a` |
| 40 | Workspace Presets | 0.32.0 | `8197f32` |
| 41 | Activity Log + Toasts | 0.33.0 | `f1db945` |
| 42 | Ops Metrics Panel | 0.34.0 | `34bfac5` |
| 43 | Red-team Workbench Hardening | 0.35.0 | `2b90b1f` |
| 44 | E2E Paper Workflow Integration | 0.36.0 | `df89295` |
| 45 | About Dialog + Version Badge | 0.37.0 | `a103236` |
| 46 | Multi-Session Switcher | 0.38.0 | `ce9cbdd` |
| 47 | Chat Context Awareness | 0.39.0 | `afdf067` |
| 48 | Theme CSS Completion | 0.40.0 | `9227750` |
| 49 | Milestone Freeze Docs + CHANGELOG | 0.41.0 | `0ddbe67` |
| 50 | Performance Baseline Workbench API | 0.42.0 | `d91f239` |
| 51 | API Rate Limit (loopback soft) | 0.43.0 | `2451802` |
| 52 | Graceful Shutdown + Paper Session Safety | 0.44.0 | `feace00` |
| 53 | Dockerfile Workbench (opt-in) | 0.45.0 | `065821b` |
| 54 | Readiness / Liveness Probes | 0.46.0 | `a34902c` |
| 55 | OpenAPI / API Catalog | 0.47.0 | `b415978` |
| 56 | Security Headers | 0.48.0 | `6246a74` |
| 57 | Content-Security-Policy | 0.49.0 | `fbb0355` |
| 58 | Milestone Freeze Docs + CHANGELOG (v0.50) | 0.50.0 | `7f6c440` |
| 59 | A11y Basics (focus + aria) | 0.51.0 | `6a1823a` |
| 60 | i18n Scaffold (es default) | 0.52.0 | `f7506c7` |
| 61 | Request Access Log | 0.53.0 | `15e1707` |
| 62 | Access Log Panel UI | 0.54.0 | `7065400` |
| 63 | Session Auto-Backup | 0.55.0 | `aa9407c` |
| 64 | Backups Panel UI | 0.56.0 | `5a7492d` |
| 65 | Blotter CSV Server Export | 0.57.0 | `d5aae45` |
| 66 | Equity Curve Snapshot | 0.58.0 | `d10c1ce` |
| 67 | Paper PnL Summary | 0.59.0 | `57b78fd` |
| 68 | Milestone Freeze Docs + CHANGELOG (v0.60) | 0.60.0 | `140eb25` |
| 69 | Risk Utilization Report | 0.61.0 | `0d9d7c7` |
| 70 | Paper Kill Switch | 0.62.0 | `2764637` |
| 71 | Health Extended + 1000 Tests | 0.63.0 | `c81a49c` |
| 72 | Desktop Notifications Hook | 0.64.0 | `1b7df41` |
| 73 | Optional Sound Alerts | 0.65.0 | `e3257b7` |
| 74 | Status Bar Clock Timezone | 0.66.0 | `ce0d5d1` |
| 75 | Broker Heartbeat Status | 0.67.0 | `c506ab6` |
| 76 | Broker Reconnect Button | 0.68.0 | `30ff7ec` |
| 77 | Broker Disconnect + Milestone prep | 0.69.0 | `f782981` |
| 78 | Milestone Freeze Docs + CHANGELOG (v0.70) | 0.70.0 | `77ea109` |
| 79 | Watchlist Import/Export JSON | 0.71.0 | `7245ca4` |
| 80 | Custom Preset Save | 0.72.0 | `67fd498` |
| 81 | Custom Preset Delete | 0.73.0 | `2975729` |
| 82 | Window Snap to Edges | 0.74.0 | `bb57bed` |
| 83 | Minimize / Restore All | 0.75.0 | 4bfb18d |
| 84 | Cascade / Tile Windows | 0.76.0 | e82ebef |
| 85 | Bring to Front / Send to Back | 0.77.0 | c1b6d43 |
| 86 | Maximize / Restore Window | 0.78.0 | b82485c |
| 87 | Broker Plugin Contract v1 | 0.79.0 | e0ff1d9 |
| 88 | Paper Journal authoritative + reconciliation | 0.80.0 | 54161f5 (+ 27dd0e2 Windows) |

---

## Invariantes Zero-Trust (no negociar)

1. Sin unlock: `assert_live_routing_blocked()` falla; `LIVE_BLOCKED` documenta fail-closed
2. Unlock LIVE solo con `QUANTLAB_LIVE_USER` / `QUANTLAB_LIVE_PASSWORD` (env local) + POST `/api/live/unlock`; password **nunca** en git ni disco de sesión
3. Con unlock scope `binance_demo`: default `local_demo_sim`; testnet remoto solo con `QUANTLAB_DEMO_USE_TESTNET=1` + `BINANCE_DEMO_*`; `live_routing=False` (no producción)
4. **REAL ≠ LIVE** — alias producto `REAL = PAPER` (MD/cuenta pueden ser reales; fills simulados)
5. Workbench bind default `127.0.0.1`; non-loopback exige `--allow-non-loopback`
6. Chat: solo tools allowlist read-only; mutaciones → `ValidationError`
7. FakeProvider default CI; LLM opt-in vía env
8. Session paths fail-closed (`validate_session_id`, zip-slip)
9. PaperBroker / Paper Session: fills simulados; sin venue submit
10. Plugins externos siempre detrás de `ReadOnlyBrokerPort`; no submit/cancel
11. Sin emitir `FASE_19`…`FASE_107_APPROVED.md` desde INTERNAL
12. `phases_summary` tip: `F19–F111 INTERNAL` (+ UX/chat post-F111 en tip de trabajo)
13. About / health `version` ≡ `__version__` (tip `1.01.0`)
14. Journal PAPER append-only; mirror demo opt-in source `binance_demo`
15. Guided Lab v1.01: alpha Binance · pipeline · chat asistente (abrir/correr sin órdenes)
16. UI: `ui_font_scale` · resize bordes wm · `tips.js` / `data-tip` / i18n `tip.*`
17. Estrategias F115: `strategy_catalog` por familia · `runnable`/`binance_ready` · stubs fail-closed · skill `strategy-expander`
18. Backtest UX: `verdict_es` + Guided Lab explica fills/equity; MM half_spread escala al mid en alts
19. Fees lab: `brokers/binance/fees.py` VIP0 Spot 10 bps (BNB opt-in via env); `run_lab_backtest` ya no usa fee=0
20. Horizonte MD lab: klines paginadas hasta **525_600** (1y@1m); aviso pesado >40k; UI default 1200
21. **FASE 0 Alpha Scanner:** auditoría en `docs/scanner/current-alpha-scanner-audit.md` + baseline sintético; sin cambio de scoring aún
22. **Alpha Scanner MD real:** `run_venue_lab_scanner` + `recommend.py` (score→familia/estrategias/TF); UI chips → `Simulador.applyPrefill`; Binance spot=listado exchange, resto=SIM_COINS vía md_router

## Próximo

- Probar Alpha Scanner en workbench (Ctrl+F5 + reiniciar) sobre Binance/OKX/HL
- Monte Carlo corrección: UI workbench actualizada (`montecarlo.js` presets 1e6, jobs async,
  cost estimate, Abrir dataset, `labMontecarloJob`/`Cancel`); backend FASE 1+ en curso
  · status: `docs/progress/montecarlo-correction-status.md`
- Deep-link por id dentro de paneles Scan/BT (si aparece API de foco)
- Selector fecha start/end opcional (hoy: últimas N hasta ahora)
- Certificados externos F19+ (Meta-Auditor)

## Checkpoint

Ver `RETOMAR.txt` en la raíz — pegar en Cursor: `seguí desde donde quedaste — autónomo`
