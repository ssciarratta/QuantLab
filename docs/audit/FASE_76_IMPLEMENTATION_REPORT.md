# FASE 76 — Implementation Report (Broker Reconnect Button)

**Fecha:** 2026-07-26  
**Versión:** 0.68.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F75 Broker Heartbeat Status  
**Impl SHA:** *(tip post-commit)*  
**Alcance:** POST `/api/broker/reconnect` + last connect meta + UI Market/Health — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Persist + reconnect helpers | `workbench/broker_reconnect.py` |
| D2 | API connect/reconnect | `workbench/api.py` · `server.py` · `api_catalog.py` |
| D3 | QLApi + UI | `static/js/api.js` · `panes/market.js` · `panes/health.js` |
| D4 | Spec + DEC-120 + bump | `docs/FASE_76_RECONNECT.md` · **0.68.0** |
| D5 | Suite | `tests/unit/workbench/test_broker_reconnect_f76.py` |
| D6 | Smoke F76 | `scripts/internal_audit_smoke.py` |
| D7 | Implementation report | este doc |
| D8 | Bundle default F19–F76 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_76_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-120
- `phases_summary == "F19–F76 INTERNAL"`
- About `version` ≡ `__version__` · **0.68.0**
- Reconnect sin last connect → HTTP 400
- Connect escribe `last_broker_connect` en meta

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff check src/quantlab tests scripts
uv run mypy --strict src/quantlab
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Certificado externo `FASE_76_APPROVED.md`
- Auto-reconnect en heartbeat fail
- Secrets / API keys en meta
