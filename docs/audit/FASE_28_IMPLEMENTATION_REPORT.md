# FASE 28 — Implementation Report (Layout Persistence + Journal)

**Fecha:** 2026-07-26  
**Versión:** 0.20.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F27 Strategy Catalog · F20 Workbench WM · F23 session durable  
**Alcance:** layout MDI por sesión + panel Journal fills — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| L1 | Layout save/load | `workbench/layout.py` |
| L2 | Session `layout_path` | `workbench/session.py` |
| A1 | `GET`/`PUT` `/api/layout` | `api.py` + `server.py` (`do_PUT`) |
| U1 | Debounce save + restore | `static/js/wm.js`, `shell.js`, `api.js` |
| U2 | Panel Journal + CSV | `static/js/panes/journal.js` + `index.html` |
| T1 | Tests layout + API | `tests/unit/workbench/test_layout_f28.py` |
| D1 | Spec + DEC-072 + bump | `docs/FASE_28_LAYOUT_JOURNAL.md` · `0.20.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Layout fail-closed (ids / rangos / version)
- Journal lee solo fills paper de sesión
- Nunca place_order venue
- DEC-072

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_layout_f28.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Export CSV server-side
- Órdenes venue / auto-flip LIVE
