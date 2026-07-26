# FASE 20 — Implementation Report (Workbench)

**Fecha:** 2026-07-26  
**Versión:** 0.12.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Alcance:** SPA local + API loopback — **sin chat**, **sin paneles F21**, **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| W1 | CLI `quantlab-workbench` | `workbench/launch.py` |
| W2 | `ThreadingHTTPServer` | `workbench/server.py` |
| W3 | JSON API + `WorkbenchState` | `workbench/api.py` |
| W4 | SPA + window-manager | `workbench/static/` |
| W5 | Paneles Health / MD / Blotter | `static/js/panes/` |
| W6 | Suite unit | `tests/unit/workbench/` |
| W7 | Spec DoD | `docs/FASE_20_WORKBENCH.md` |

## Diseño

- stdlib only (`http.server`) — sin deps nuevas en `pyproject`
- Sesión: `OperatingMode` + `BrokerRegistry` + `PaperBroker` + `PaperFillJournal`
- Connect siempre envuelve MD en `PaperBroker` (nunca `place_order` venue)
- POST `/api/mode` con `live` → HTTP 400
- UI: desktop metaphor, labels ES, slate + amber terminal

## Invariantes

- `LIVE_BLOCKED is True`
- Bind default `127.0.0.1`
- Paper path ≠ live venue routing

## QA

```text
uv sync --extra dev
uv run ruff format/check …
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench tests/unit/brokers -q
uv run quantlab-health
```

## Fuera de alcance (correcto)

- Chat IA → F22  
- Backtest/optimizer panes → F21  
- Flip `LIVE_BLOCKED`
