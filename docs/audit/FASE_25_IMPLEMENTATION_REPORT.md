# FASE 25 — Implementation Report (Ops Desk)

**Fecha:** 2026-07-26  
**Versión:** 0.17.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F23 Paper Book · F24 Venue plugins  
**Alcance:** 1-click launcher + hardening M1/M2 + paper slip + Risk UI — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| L1 | Launcher 1-click | `scripts/launch_workbench.sh` |
| L2 | Desktop entry | `packaging/quantlab-workbench.desktop` |
| L3 | Ops doc | `docs/ops/WORKBENCH_1CLICK.md` |
| H1 | Non-loopback gate | `workbench/launch.py` (`--allow-non-loopback`) |
| H2 | experiment_id charset | `workbench/lab_services.py` (`validate_experiment_id`) |
| P1 | Paper slippage_bps | `brokers/paper/broker.py` + API/CLI |
| U1 | Risk panel | `static/js/panes/risk.js` + `GET /api/risk` |
| S1 | Smoke extendido | `scripts/internal_audit_smoke.py` |
| T1 | Tests | `test_launch_non_loopback.py`, `test_experiment_id_charset.py`, `test_paper_slippage_bps.py` |
| D1 | Spec DoD + bump | `docs/FASE_25_OPS_DESK.md` · `0.17.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Bind default `127.0.0.1`; non-loopback sin flag → exit 2
- `experiment_id` solo `[A-Za-z0-9_-]+`
- Slippage paper adverso (BUY ↑ / SELL ↓); default `0`
- Banner `session_id` + menú Inicio → Riesgo

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/brokers tests/unit/workbench scripts
uv run ruff check src/quantlab tests/unit/brokers tests/unit/workbench scripts
uv run mypy --strict src/quantlab
uv run pytest tests/unit/brokers tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

**Audit INTERNAL (2026-07-26):** mypy 156 · ruff · **552** pytest · health 0.17.0 · smoke 11 PASS · **APROBADO_INTERNO**  
(`docs/audit/INTERNAL_AUDIT_F25.md`; sin `FASE_25_APPROVED.md`)

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Electron / auth WAN
- Órdenes venue / LIVE
- DEC-069 registrada en `learning/decisiones.txt`