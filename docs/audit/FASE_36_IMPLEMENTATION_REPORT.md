# FASE 36 — Implementation Report (Settings + Status Bar)

**Fecha:** 2026-07-26  
**Versión:** 0.28.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F35 Command Palette · F28 Layout · F27 Strategy Catalog  
**Alcance:** settings durables + status bar — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| S1 | Persistencia settings | `workbench/settings.py` |
| S2 | Session `settings_path` | `workbench/session.py` |
| A1 | `GET/PUT /api/settings` | `api.py` + `server.py` |
| U1 | Panel Settings JS | `static/js/panes/settings.js` |
| U2 | Status bar + shell | `static/index.html` · `shell.js` |
| U3 | Theme CSS | `static/css/workbench.css` |
| U4 | Commands + API client | `commands.py` · `api.js` |
| T1 | Tests F36 | `tests/unit/workbench/test_settings_f36.py` |
| T2 | Smoke F36 | `scripts/internal_audit_smoke.py` |
| D1 | Spec + DEC-080 + bump | `docs/FASE_36_SETTINGS.md` · `0.28.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Locale solo `es`
- Theme solo `slate` \| `high-contrast`
- Strategy fail-closed (catálogo F27)
- Sin flip LIVE / place_order / set_live
- DEC-080

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_settings_f36.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Certificado externo `FASE_36_APPROVED.md`
