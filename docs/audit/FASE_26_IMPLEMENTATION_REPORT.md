# FASE 26 — Implementation Report (Paper Session Runner)

**Fecha:** 2026-07-26  
**Versión:** 0.18.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F23 Paper Book · F24 Venue plugins · F25 Ops Desk  
**Alcance:** sesión paper operativa (estrategia → risk → PaperBroker) — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| R1 | `PaperSessionConfig` + `PaperSessionRunner` | `workbench/paper_session.py` |
| R2 | Buffer barras sintéticas desde snapshot | `snapshot_to_bar` |
| R3 | Estrategias research | dummy / buy_once / momentum |
| A1 | API session start/stop/step/status | `workbench/api.py` + `server.py` |
| U1 | Panel Sesión Paper + menú Inicio | `static/js/panes/paper_session.js` |
| T1 | Tests runner + API | `test_paper_session_runner.py` |
| D1 | Spec DoD + bump | `docs/FASE_26_PAPER_SESSION.md` · `0.18.0` |

## Flujo `step()`

1. `broker.get_snapshot(symbol)`
2. Barra OHLC trivial (last/mid) → buffer; `StrategyContext` + portfolio desde `PaperBook`
3. `strategy.on_event` (BAR); si vacío → `on_bar`
4. Por cada intent PLACE/CANCEL: `risk.check_intent` → `broker.submit` (PaperBroker)
5. Resumen: intents, actions (ack / RISK_REJECTED), book snapshot

Background opcional: `interval_ms` → thread daemon cancelable vía `stop()`.

## Invariantes

- `LIVE_BLOCKED is True`
- Constructor / API: **solo** `PaperBroker` (`isinstance` fail-closed — H1 audit)
- Nunca `md_port.submit` / place_order venue
- Risk reject → `RISK_REJECTED` en actions (sesión sigue)
- Reconnect / cambio de modo invalida sesión paper
- DEC-070

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_paper_session_runner.py -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- WS streaming exchange real
- Auto-flip LIVE
- Órdenes venue
