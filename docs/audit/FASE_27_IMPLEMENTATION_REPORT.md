# FASE 27 — Implementation Report (Strategy Catalog)

**Fecha:** 2026-07-26  
**Versión:** 0.19.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F26 Paper Session · research InventoryMM / Avellaneda–Stoikov  
**Alcance:** catálogo estrategias workbench (paper + lab) — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| C1 | Catálogo + factory + MM adapter | `workbench/strategy_catalog.py` |
| C2 | Wire paper session | `workbench/paper_session.py` |
| C3 | Wire lab backtest + capabilities | `workbench/lab_services.py` |
| A1 | `GET /api/lab/strategies` | `api.py` + `server.py` |
| U1 | Selectores + params UI | `static/js/panes/paper_session.js`, `backtest.js` |
| T1 | Smoke por strategy_id | `tests/unit/workbench/test_strategy_catalog_f27.py` |
| D1 | Spec + DEC-071 + bump | `docs/FASE_27_STRATEGY_CATALOG.md` · `0.19.0` |

## Firmas cableadas

```text
InventoryMMStrategy(parameters: dict | None)  # quantity, half_spread, max_pos
AvellanedaStoikovStrategy(parameters: dict | None)  # gamma, sigma, kappa, horizon_events, max_pos, quantity
```

Context MM espera `best_bid` / `best_ask` / `inventory` (± `inventory_skew`) en `StrategyContext.parameters`.

## Invariantes

- `LIVE_BLOCKED is True`
- Paper session: solo `PaperBroker` (fail-closed)
- Nunca place_order venue
- DEC-071

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_strategy_catalog_f27.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- MicroBacktester 5B en UI lab
- Órdenes venue / auto-flip LIVE
