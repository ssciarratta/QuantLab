# QuantLab — PROJECT MEMORY (Cursor)

**Actualizado:** 2026-07-26  
**Branch trabajo:** `cursor/modo-real-workbench-aafd`  
**Versión tip:** **0.23.0**  
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
| F19–F31 | **APROBADO_INTERNO** Zero-Trust; externos **pendientes** |
| Arco F19–F22 | Cerrado INTERNAL → `docs/audit/INTERNAL_AUDIT_F19_F22_ARC.md` |
| Arco F23–F25 | Cerrado INTERNAL → `docs/audit/INTERNAL_AUDIT_F23_F25_ARC.md` |
| Noche F19–F31 | `docs/audit/INTERNAL_AUDIT_F19_F31_NIGHT.md` |

**Regla:** el auditor INTERNAL **no** emite `FASE_*_APPROVED.md` (reserva Meta-Auditor externo).

---

## Arco nocturno F19–F31 (SHAs impl)

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
| 31 | Feature Store Browser + Pipeline Runner | 0.23.0 | `70a8ee2` |

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

---

## Paths clave

- Roadmap: `docs/ROADMAP_ALIGNED.md`
- Mapa auditor: `docs/audit/MAPA_FASES_PARA_AUDITOR.md`
- Resumen: `RESUMEN_PROYECTO.txt`
- DECs: `learning/decisiones.txt` (DEC-054…075)
- Workbench: `src/quantlab/workbench/`
- Feature store browser: `src/quantlab/workbench/feature_store_browser.py`
- Layout: `src/quantlab/workbench/layout.py`
- Strategy catalog: `src/quantlab/workbench/strategy_catalog.py`
- Paper session: `src/quantlab/workbench/paper_session.py`
- Launcher 1-click: `scripts/launch_workbench.sh` · `docs/ops/WORKBENCH_1CLICK.md`
- Chat: `src/quantlab/workbench/chat/`
- Smoke: `scripts/internal_audit_smoke.py`
- Bundle INTERNAL: `scripts/build_internal_review_bundle.py` (default F19–F31)
- Flip checklist (no ejecutar): `docs/ops/LIVE_FLIP_CHECKLIST.md`

---

## QA canónica

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run mypy --strict src/quantlab
uv run ruff check src/quantlab tests scripts
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

---

## Entry points útiles

- `quantlab-health` — ops / LIVE gate
- `quantlab-workbench` / `./scripts/launch_workbench.sh` — UI local F20–F31
- `quantlab-a3` — market data A3 (anticorrupción)
- `quantlab-vertical-slice` — slice mínimo
