# Milestone Freeze — Workbench F19–F77 + F78 (v0.70.0)

**Fecha freeze docs:** 2026-07-26  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Milestone tip (hito 0.70):** **v0.70.0** (F78 Milestone Freeze Docs)  
**Último producto previo:** **v0.69.0** (F77 Broker Disconnect · impl `f782981`)  
**LIVE:** **BLOQUEADO** (`LIVE_BLOCKED=True`) · flip **NO**  
**Certificados externos F19–F78:** **NO emitidos** (reserva Meta-Auditor)

> Freeze documental del arco workbench F19–F77 (producto) + F78 (milestone sync).  
> No habilita LIVE. Spec F78: `docs/FASE_78_MILESTONE_V070.md`.

---

## Inventario F19–F77 / F78

| Fase | Tema | Ver | Impl SHA | INTERNAL |
|------|------|-----|----------|----------|
| **19** | OperatingMode + BrokerPort; REAL=PAPER | 0.11.0 | `a5b12d3` | APROBADO_INTERNO |
| **20** | Workbench stdlib loopback + SPA WM | 0.12.0 | `cacf8e6` | APROBADO_INTERNO |
| **21** | Lab panels `/api/lab/*` | 0.13.0 | `c397ffc` | APROBADO_INTERNO |
| **22** | Chat IA allowlist + FakeProvider | 0.14.0 | `5ef9866` | APROBADO_INTERNO |
| **23** | PaperBook + sesión + risk | 0.15.0 | `9b89274` | APROBADO_INTERNO |
| **24** | Venue plugins + MD read-only | 0.16.0 | `c846e81` | APROBADO_INTERNO |
| **25** | Ops Desk 1-click + hardening | 0.17.0 | `21fe144` | APROBADO_INTERNO |
| **26** | Paper Session Runner | 0.18.0 | `46487a4` | APROBADO_INTERNO |
| **27** | Strategy Catalog (MM + AS) | 0.19.0 | `244a3fb` | APROBADO_INTERNO |
| **28** | Layout persistence + Journal | 0.20.0 | `86517cf` | APROBADO_INTERNO |
| **29** | Report Viewer + Metrics History | 0.21.0 | `2f37bf7` | APROBADO_INTERNO |
| **30** | Universe Watchlist + Data Catalog | 0.22.0 | `7d8bf88` | APROBADO_INTERNO |
| **31** | Feature Store Browser + Pipeline | 0.23.0 | `70a8ee2` | APROBADO_INTERNO |
| **32** | Validation / Walk-Forward Runner UI | 0.24.0 | `8c1cf58` | APROBADO_INTERNO |
| **33** | Optimizer History + Pareto Panel | 0.25.0 | `c39a57f` | APROBADO_INTERNO |
| **34** | Monte Carlo History + HB Export | 0.26.0 | `18cea7c` | APROBADO_INTERNO |
| **35** | Command Palette + Keyboard Shortcuts | 0.27.0 | `314b2cd` | APROBADO_INTERNO |
| **36** | Settings + Status Bar | 0.28.0 | `2c0cb11` | APROBADO_INTERNO |
| **37** | First-run Onboarding Wizard | 0.29.0 | `81ff9b1` | APROBADO_INTERNO |
| **38** | Docs / Help Browser | 0.30.0 | `becd116` | APROBADO_INTERNO |
| **39** | Session Export/Import ZIP | 0.31.0 | `0cb9d7a` | APROBADO_INTERNO |
| **40** | Workspace Presets | 0.32.0 | `8197f32` | APROBADO_INTERNO |
| **41** | Activity Log + Toasts | 0.33.0 | `f1db945` | APROBADO_INTERNO |
| **42** | Ops Metrics Panel | 0.34.0 | `34bfac5` | APROBADO_INTERNO |
| **43** | Red-team Workbench Hardening | 0.35.0 | `2b90b1f` | APROBADO_INTERNO |
| **44** | E2E Paper Workflow Integration | 0.36.0 | `df89295` | APROBADO_INTERNO |
| **45** | About Dialog + Version Badge | 0.37.0 | `a103236` | APROBADO_INTERNO |
| **46** | Multi-Session Switcher | 0.38.0 | `ce9cbdd` | APROBADO_INTERNO |
| **47** | Chat Context Awareness | 0.39.0 | `afdf067` | APROBADO_INTERNO |
| **48** | Theme CSS Completion | 0.40.0 | `9227750` | APROBADO_INTERNO |
| **49** | Milestone Freeze Docs + CHANGELOG (v0.40) | 0.41.0 | `0ddbe67` | APROBADO_INTERNO |
| **50** | Performance Baseline Workbench API | 0.42.0 | `d91f239` | APROBADO_INTERNO |
| **51** | API Rate Limit (loopback soft) | 0.43.0 | `2451802` | APROBADO_INTERNO |
| **52** | Graceful Shutdown + Paper Session Safety | 0.44.0 | `feace00` | APROBADO_INTERNO |
| **53** | Dockerfile Workbench (opt-in) | 0.45.0 | `065821b` | APROBADO_INTERNO |
| **54** | Readiness / Liveness Probes | 0.46.0 | `a34902c` | APROBADO_INTERNO |
| **55** | OpenAPI / API Catalog | 0.47.0 | `b415978` | APROBADO_INTERNO |
| **56** | Security Headers | 0.48.0 | `6246a74` | APROBADO_INTERNO |
| **57** | Content-Security-Policy | 0.49.0 | `fbb0355` | APROBADO_INTERNO |
| **58** | Milestone Freeze Docs + CHANGELOG (v0.50) | 0.50.0 | `7f6c440` | APROBADO_INTERNO |
| **59** | A11y Basics (focus + aria) | 0.51.0 | `6a1823a` | APROBADO_INTERNO |
| **60** | i18n Scaffold (es default) | 0.52.0 | `f7506c7` | APROBADO_INTERNO |
| **61** | Request Access Log | 0.53.0 | `15e1707` | APROBADO_INTERNO |
| **62** | Access Log Panel UI | 0.54.0 | `7065400` | APROBADO_INTERNO |
| **63** | Session Auto-Backup | 0.55.0 | `aa9407c` | APROBADO_INTERNO |
| **64** | Backups Panel UI | 0.56.0 | `5a7492d` | APROBADO_INTERNO |
| **65** | Blotter CSV Server Export | 0.57.0 | `d5aae45` | APROBADO_INTERNO |
| **66** | Equity Curve Snapshot | 0.58.0 | `d10c1ce` | APROBADO_INTERNO |
| **67** | Paper PnL Summary | 0.59.0 | `57b78fd` | APROBADO_INTERNO |
| **68** | Milestone Freeze Docs + CHANGELOG (v0.60) | 0.60.0 | `140eb25` | APROBADO_INTERNO |
| **69** | Risk Utilization Report | 0.61.0 | `0d9d7c7` | APROBADO_INTERNO |
| **70** | Paper Kill Switch | 0.62.0 | `2764637` | APROBADO_INTERNO |
| **71** | Health Extended + 1000 Tests Milestone | 0.63.0 | `c81a49c` | APROBADO_INTERNO |
| **72** | Desktop Notifications Hook | 0.64.0 | `1b7df41` | APROBADO_INTERNO |
| **73** | Optional Sound Alerts | 0.65.0 | `e3257b7` | APROBADO_INTERNO |
| **74** | Status Bar Clock Timezone | 0.66.0 | `ce0d5d1` | APROBADO_INTERNO |
| **75** | Broker Heartbeat Status | 0.67.0 | `c506ab6` | APROBADO_INTERNO |
| **76** | Broker Reconnect Button | 0.68.0 | `30ff7ec` | APROBADO_INTERNO |
| **77** | Broker Disconnect + Milestone prep | 0.69.0 | `f782981` | APROBADO_INTERNO |
| **78** | Milestone Freeze Docs + CHANGELOG (v0.70) | 0.70.0 | `77ea109` | APROBADO_INTERNO |

### Arcos INTERNAL

| Arco | Doc |
|------|-----|
| F19–F22 | `INTERNAL_AUDIT_F19_F22_ARC.md` |
| F23–F25 | `INTERNAL_AUDIT_F23_F25_ARC.md` |
| Freeze F19–F48 | `MILESTONE_V040_FREEZE.md` |
| Freeze F19–F57/F58 | `MILESTONE_V050_FREEZE.md` |
| Freeze F19–F67/F68 | `MILESTONE_V060_FREEZE.md` |
| Noche F19–F77 | `INTERNAL_AUDIT_F19_F77_NIGHT.md` |
| Noche F19–F78 | `INTERNAL_AUDIT_F19_F78_NIGHT.md` |
| Freeze F19–F77/F78 | este documento |

---

## Invariantes (no negociar)

1. `LIVE_BLOCKED is True` — sin flip, sin `place_order` venue LIVE
2. **REAL ≠ LIVE** — alias producto `REAL = PAPER`
3. Workbench bind default `127.0.0.1`; non-loopback exige `--allow-non-loopback`
4. Chat: tools allowlist read-only; mutaciones / trading tools → rechazo
5. FakeProvider default CI; LLM solo opt-in vía env
6. Session paths fail-closed (`validate_session_id`, zip-slip, path traversal)
7. PaperBroker / Paper Session: fills simulados; sin venue submit
8. Sin emitir `FASE_19`…`FASE_78_APPROVED.md` desde INTERNAL
9. `phases_summary` tip: `F19–F78 INTERNAL`
10. About / health `version` ≡ `quantlab.__version__` y **startswith `0.70`**
11. CSP F57 + security headers F56 + probes F54 + rate limit F51 intactos
12. Soft rate limit / graceful shutdown / Docker opt-in: sin auth WAN
13. Paper kill F70 + risk util F69 + PnL F67 + equity F66 + blotter CSV F65 intactos
14. Broker heartbeat F75 + reconnect F76 + disconnect F77 intactos (paper/research)

---

## Cómo operar (research / paper)

```bash
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run quantlab-health                  # ok · live_blocked=true · version 0.70.x
./scripts/launch_workbench.sh --no-browser
# http://127.0.0.1:8765  ·  --mode tester|paper|real  ·  live rechazado
uv run python scripts/internal_audit_smoke.py
# Docker opt-in (solo Desktop port-map loopback):
# docker build -f Dockerfile.workbench -t quantlab-workbench:0.70.0 .
# docker run --rm -p 127.0.0.1:8765:8765 quantlab-workbench:0.70.0
```

| Acción | Notas |
|--------|-------|
| Modos | `tester` / `paper` / `real`(=paper); `live` rechazado |
| MD | venues `a3` / `binance` / `generic_*` + plugins; `md_source` fake\|env |
| Lab | backtest / features / validation / optimize / MC / HB export — sintético o sesión |
| Chat | FakeProvider; resumen sesión / reports / estrategias (F47) |
| Themes | `slate` (default) \| `high-contrast` (F48) |
| Sessions | multi-session switcher (F46); export/import ZIP (F39); auto-backup (F63–F64) |
| Paper | equity (F66); PnL (F67); fills CSV (F65); kill switch (F70); risk util (F69) |
| Broker ops | heartbeat (F75); reconnect (F76); disconnect (F77) — sin LIVE |
| Ops | probes `/api/livez` `/api/readyz` (F54); OpenAPI `/api/openapi.json` (F55); access log (F61–F62) |
| Hardening | rate limit soft (F51); shutdown seguro (F52); headers+CSP (F56–F57); a11y (F59); i18n es (F60) |
| UX alerts | desktop notifications opt-in (F72); sound alerts opt-in (F73); clock TZ (F74) |

---

## Límites (NO LIVE)

| Límite | Estado |
|--------|--------|
| Order routing LIVE / venue submit real | **BLOQUEADO** |
| Flip `LIVE_BLOCKED` | **NO** en este milestone |
| Auth WAN / bind público sin flag | **NO** (fail-closed) |
| Certificados externos F19+ | Solo Meta-Auditor externo |
| Electron / desktop packaging | Fuera de alcance |
| Locales ≠ `es` (completos) | Stub `en` solamente (F60) |

Checklist flip (referencia, **no ejecutar**): `docs/ops/LIVE_FLIP_CHECKLIST.md`.

---

## QA tip (canónica)

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

Smoke tip incluye: `LIVE_BLOCKED is True` · About≡`__version__` · **version starts with 0.70**.

---

## Evidencia

| Artifact | Path |
|----------|------|
| Spec F78 | `docs/FASE_78_MILESTONE_V070.md` |
| Noche F19–F78 | `docs/audit/INTERNAL_AUDIT_F19_F78_NIGHT.md` |
| Bundle tip | `reports/QuantLab_Internal_Review_F19_F78_v0.70.0.zip` |
| CHANGELOG agrupado | `CHANGELOG.md` → `[0.70.0]` + resumen F19–F77 |

---

## Firma freeze

Milestone F19–F77 (producto ≤0.69.0) + F78 tip **0.70.0** documentado · **LIVE_BLOCKED** intacto · **sin** certificados externos
