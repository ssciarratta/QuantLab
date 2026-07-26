# QuantLab — PROJECT MEMORY (Cursor)

**Actualizado:** 2026-07-26  
**Branch trabajo:** `cursor/modo-real-workbench-aafd`  
**Versión tip:** **0.61.0** (F69 Risk Utilization Report)  
**Milestone congelado v0.40:** F19–F48 · `docs/audit/MILESTONE_V040_FREEZE.md`  
**Milestone congelado v0.50:** F19–F57/F58 · `docs/audit/MILESTONE_V050_FREEZE.md`  
**Milestone congelado v0.60:** F19–F67/F68 · `docs/audit/MILESTONE_V060_FREEZE.md`  
**LIVE:** `LIVE_BLOCKED = True` (flip **NO** ejecutado)

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
| F69 | Risk Utilization Report · **0.61.0** |
| Arco F19–F22 | `docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md` |
| Arco F23–F25 | `docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md` |
| Noche F19–F69 | `docs/audit/INTERNAL_AUDIT_F19_F69_NIGHT.md` |

**Regla:** el auditor INTERNAL **no** emite `FASE_*_APPROVED.md` (reserva Meta-Auditor externo).

---

## Arco nocturno F19–F69 (SHAs impl) — tip v0.61.0

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
| 69 | Risk Utilization Report | 0.61.0 | *(tip)* |

---

## Invariantes Zero-Trust (no negociar)

1. `LIVE_BLOCKED is True` en `execution/live_gate.py`
2. **REAL ≠ LIVE** — alias producto `REAL = PAPER` (MD/cuenta pueden ser reales; fills simulados)
3. Workbench bind default `127.0.0.1`; non-loopback exige `--allow-non-loopback`
4. Chat: solo tools allowlist read-only; mutaciones → `ValidationError`
5. FakeProvider = default CI; LLM solo opt-in vía env (`DISABLED` por defecto)
6. Lab demos sintéticos; export HB path-safe; `experiment_id` charset `^[A-Za-z0-9_-]+$`
7. PaperBroker no llama venue submit; slip paper adverso opcional
8. Paper Session Runner: **solo PaperBroker** + risk en PLACE; sin venue submit
9. Strategy Catalog: factory compartida paper+lab; MM bar-backtest sintético; sin LIVE
10. Layout fail-closed (`layout.json`); Journal = lectura fills paper + CSV local
11. Catalog / Feature Store: read-only list; persist features solo sandbox sesión
12. About / health `version` ≡ `quantlab.__version__` (F49); tip **startswith 0.61** (F69)
13. Perf baseline F50: p95/max endpoints clave < 500ms loopback
14. Soft rate limit F51: token bucket IP/path; default 120 rps; 429 JSON
15. CSP F57 + security headers F56 + probes F54 intactos
16. A11y F59: dialog roles + aria taskbar + focus trap palette + skip link
17. i18n F60 es default; access log F61–F62; backups F63–F64
18. Paper analytics F65–F67: fills CSV · equity curve · PnL summary
19. Risk utilization F69: `%` max_qty/notional vs book en panel Risk

---

## Paths clave

- Freeze milestone v0.40: `docs/audit/MILESTONE_V040_FREEZE.md`
- Freeze milestone v0.50: `docs/audit/MILESTONE_V050_FREEZE.md`
- Freeze milestone v0.60: `docs/audit/MILESTONE_V060_FREEZE.md`
- Roadmap: `docs/ROADMAP_ALIGNED.md`
- Mapa auditor: `docs/audit/MAPA_FASES_PARA_AUDITOR.md`
- Noche tip: `docs/audit/INTERNAL_AUDIT_F19_F69_NIGHT.md`
- LIVE flip (NO ejecutar): `docs/ops/LIVE_FLIP_CHECKLIST.md`
