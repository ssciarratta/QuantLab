# QuantLab — PROJECT MEMORY (Cursor)

**Actualizado:** 2026-07-26  
**Branch trabajo:** `cursor/modo-real-workbench-aafd`  
**Versión tip:** **0.80.0** (F88 Paper Journal authoritative + reconciliation)
**Milestone congelado v0.40:** F19–F48 · `docs/audit/MILESTONE_V040_FREEZE.md`  
**Milestone congelado v0.50:** F19–F57/F58 · `docs/audit/MILESTONE_V050_FREEZE.md`  
**Milestone congelado v0.60:** F19–F67/F68 · `docs/audit/MILESTONE_V060_FREEZE.md`  
**Milestone congelado v0.70:** F19–F77/F78 · `docs/audit/MILESTONE_V070_FREEZE.md`  
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
| Noche F19–F88 | `docs/audit/INTERNAL_AUDIT_F19_F88_NIGHT.md` |

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

1. `LIVE_BLOCKED is True` en `execution/live_gate.py`
2. **REAL ≠ LIVE** — alias producto `REAL = PAPER` (MD/cuenta pueden ser reales; fills simulados)
3. Workbench bind default `127.0.0.1`; non-loopback exige `--allow-non-loopback`
4. Chat: solo tools allowlist read-only; mutaciones → `ValidationError`
5. FakeProvider default CI; LLM opt-in vía env
6. Session paths fail-closed (`validate_session_id`, zip-slip)
7. PaperBroker / Paper Session: fills simulados; sin venue submit
8. Plugins externos siempre detrás de `ReadOnlyBrokerPort`; no submit/cancel
9. Sin emitir `FASE_19`…`FASE_88_APPROVED.md` desde INTERNAL
10. `phases_summary` tip: `F19–F88 INTERNAL`
11. About / health `version` ≡ `__version__` y startswith `0.80`
12. Journal PAPER append-only autoritativo; rebuild solo CLI offline con backup

## Próximo

- Certificados externos F19–F88 solo con Meta-Auditor externo
- F89: Milestone Freeze Docs v0.80 (0.81.0) → F90 Reconciliation UI (0.82.0)
- Flip LIVE solo con checklist + Meta-Auditor + dueño + commit dedicado
