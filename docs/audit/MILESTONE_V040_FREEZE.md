# Milestone Freeze — Workbench F19–F48 (v0.40.0)

**Fecha freeze docs:** 2026-07-26  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Milestone código congelado:** **v0.40.0** (F48 Theme CSS Completion)  
**Versión tip post-freeze (F49):** **0.41.0** (docs/milestone sync — este documento + CHANGELOG)  
**LIVE:** **BLOQUEADO** (`LIVE_BLOCKED=True`) · flip **NO**  
**Certificados externos F19–F48:** **NO emitidos** (reserva Meta-Auditor)

> Freeze documental del arco workbench F19–F48. No habilita LIVE.  
> Spec F49: `docs/FASE_49_MILESTONE.md`.

---

## Inventario F19–F48

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

### Arcos INTERNAL

| Arco | Doc |
|------|-----|
| F19–F22 | `INTERNAL_AUDIT_F19_F22_ARC.md` |
| F23–F25 | `INTERNAL_AUDIT_F23_F25_ARC.md` |
| Noche F19–F48 | `INTERNAL_AUDIT_F19_F48_NIGHT.md` |

---

## Invariantes (no negociar)

1. `LIVE_BLOCKED is True` — sin flip, sin `place_order` venue LIVE
2. **REAL ≠ LIVE** — alias producto `REAL = PAPER`
3. Workbench bind default `127.0.0.1`; non-loopback exige `--allow-non-loopback`
4. Chat: tools allowlist read-only; mutaciones / trading tools → rechazo
5. FakeProvider default CI; LLM solo opt-in vía env
6. Session paths fail-closed (`validate_session_id`, zip-slip, path traversal)
7. PaperBroker / Paper Session: fills simulados; sin venue submit
8. Sin emitir `FASE_19`…`FASE_48_APPROVED.md` desde INTERNAL
9. `phases_summary` tip post-F49: `F19–F49 INTERNAL`
10. About `version` ≡ `quantlab.__version__`

---

## Cómo operar (research / paper)

```bash
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run quantlab-health                  # ok · live_blocked=true · version tip
./scripts/launch_workbench.sh --no-browser
# http://127.0.0.1:8765  ·  --mode tester|paper|real  ·  live rechazado
uv run python scripts/internal_audit_smoke.py
```

| Acción | Notas |
|--------|-------|
| Modos | `tester` / `paper` / `real`(=paper); `live` rechazado |
| MD | venues `a3` / `binance` / `generic_*` + plugins; `md_source` fake\|env |
| Lab | backtest / features / validation / optimize / MC / HB export — sintético o sesión |
| Chat | FakeProvider; resumen sesión / reports / estrategias (F47) |
| Themes | `slate` (default) \| `high-contrast` (F48) |
| Sessions | multi-session switcher (F46); export/import ZIP (F39) |

---

## Límites (NO LIVE)

| Límite | Estado |
|--------|--------|
| Order routing LIVE / venue submit real | **BLOQUEADO** |
| Flip `LIVE_BLOCKED` | **NO** en este milestone |
| Auth WAN / bind público sin flag | **NO** (fail-closed) |
| Certificados externos F19+ | Solo Meta-Auditor externo |
| Electron / desktop packaging | Fuera de alcance |
| Locales ≠ `es` | Fuera de alcance tip |

Checklist flip (referencia, **no ejecutar**): `docs/ops/LIVE_FLIP_CHECKLIST.md`.

---

## Evidencia

| Artifact | Path |
|----------|------|
| Spec F49 | `docs/FASE_49_MILESTONE.md` |
| Noche F19–F48 | `docs/audit/INTERNAL_AUDIT_F19_F48_NIGHT.md` |
| Bundle tip | `reports/QuantLab_Internal_Review_F19_F49_v0.41.0.zip` |
| CHANGELOG agrupado | `CHANGELOG.md` → `[0.41.0]` + resumen F19–F48 |

---

## Firma freeze

Milestone F19–F48 (v0.40.0) documentado · tip F49 **0.41.0** · **LIVE_BLOCKED** intacto · **sin** certificados externos
