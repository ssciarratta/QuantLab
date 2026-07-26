# FASE 86 — Implementation Report (Maximize / Restore Window)

**Fecha:** 2026-07-26  
**Versión:** 0.78.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F85 Bring to Front / Send to Back v0.77  
**Impl SHA:** `aa6266f`  
**Alcance:** Maximize / Restore Window — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | `maximize` / `restoreFromMaximize` / `toggleMaximize` + preMax + titlebar btn/dblclick | `static/js/wm.js` |
| D2 | Restore `maximized` on open + `mergeOpts` | `wm.js` · `shell.js` |
| D3 | Commands registry | `workbench/commands.py` |
| D4 | Palette + menú Inicio + i18n + CSS | `command_palette.js` · `shell.js` · `index.html` · `i18n.js` · `workbench.css` |
| D5 | Layout `maximized` bool | `workbench/layout.py` |
| D6 | Spec + DEC-130 + bump | `docs/FASE_86_MAXIMIZE.md` · **0.78.0** |
| D7 | Suite | `tests/unit/workbench/test_maximize_f86.py` |
| D8 | Smoke F86 | `scripts/internal_audit_smoke.py` |
| D9 | Implementation report | este doc |
| D10 | Bundle default F19–F86 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_86_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-130
- `phases_summary == "F19–F86 INTERNAL"`
- About `version` ≡ `__version__` · **0.78.0**
- Commands API incluye `action.maximize_window` + `action.restore_from_maximize`
- Persist `maximized` vía `scheduleSave()` post maximize/restore

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
- Certificado externo `FASE_86_APPROVED.md`
- Browser E2E
