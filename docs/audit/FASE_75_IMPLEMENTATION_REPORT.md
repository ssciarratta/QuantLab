# FASE 75 — Implementation Report (Broker Heartbeat Status)

**Fecha:** 2026-07-26  
**Versión:** 0.67.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F74 Status Bar Clock Timezone · F36 Settings + Status Bar  
**Impl SHA:** `c506ab6`  
**Alcance:** GET `/api/broker/heartbeat` + status bar ok/fail + poll N=5s — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | API heartbeat | `workbench/api.py` · `server.py` · `api_catalog.py` |
| D2 | QLApi client | `static/js/api.js` |
| D3 | Status bar + poll | `index.html` · `shell.js` · CSS · i18n |
| D4 | Spec + DEC-119 + bump | `docs/FASE_75_HEARTBEAT.md` · **0.67.0** |
| D5 | Suite | `tests/unit/workbench/test_broker_heartbeat_f75.py` |
| D6 | Smoke F75 | `scripts/internal_audit_smoke.py` |
| D7 | Implementation report | este doc |
| D8 | Bundle default F19–F75 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_75_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-119
- `phases_summary == "F19–F75 INTERNAL"`
- About `version` ≡ `__version__` · **0.67.0**
- `HEARTBEAT_POLL_SECONDS == 5`
- disconnected → status `disconnected` · health null (no 400)

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
- Certificado externo `FASE_75_APPROVED.md`
- Settings UI para N (constante 5s)
