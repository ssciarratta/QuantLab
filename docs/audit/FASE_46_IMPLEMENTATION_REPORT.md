# FASE 46 — Implementation Report (Multi-Session Switcher)

**Fecha:** 2026-07-26  
**Versión:** 0.38.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F45 About Dialog + Version Badge  
**Impl SHA:** `ce9cbdd`  
**Alcance:** list/switch/new sessions — **sin flip LIVE** · **sin browser**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| T1 | list_sessions + WorkbenchState switch/new | `session.py` · `api.py` |
| T2 | HTTP routes | `server.py` |
| T3 | UI panel Sessions | `sessions.js` · `shell.js` · `index.html` · CSS |
| T4 | Command `open.sessions` | `commands.py` |
| T5 | Suite F46 | `tests/unit/workbench/test_sessions_f46.py` |
| T6 | Smoke F46 | `scripts/internal_audit_smoke.py` |
| D1 | Spec + DEC-090 + bump | `docs/FASE_46_SESSIONS.md` · `0.38.0` |
| D2 | Implementation report | este doc |
| D3 | Bundle default to-phase 46 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_46_APPROVED.md`
- Sin flip LIVE / place_order venue
- Sin browser / Playwright
- DEC-090
- `phases_summary == "F19–F46 INTERNAL"`
- Switch fail-closed: `validate_session_id` + sesión existente

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_sessions_f46.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Delete/rename session
- Certificado externo `FASE_46_APPROVED.md`
