# FASE 83 — Implementation Report (Minimize / Restore All)

**Fecha:** 2026-07-26  
**Versión:** 0.75.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F82 Window Snap to Edges v0.74  
**Impl SHA:** `4bfb18d`  
**Alcance:** Minimize all / Restore all windows — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | `minimizeAll` / `restoreAll` + persist | `static/js/wm.js` |
| D2 | Commands registry | `workbench/commands.py` |
| D3 | Palette + menú Inicio + i18n | `command_palette.js` · `shell.js` · `index.html` · `i18n.js` |
| D4 | Spec + DEC-127 + bump | `docs/FASE_83_MINIMIZE_ALL.md` · **0.75.0** |
| D5 | Suite | `tests/unit/workbench/test_minimize_all_f83.py` |
| D6 | Smoke F83 | `scripts/internal_audit_smoke.py` |
| D7 | Implementation report | este doc |
| D8 | Bundle default F19–F83 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_83_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-127
- `phases_summary == "F19–F83 INTERNAL"`
- About `version` ≡ `__version__` · **0.75.0**
- Commands API incluye `action.minimize_all` + `action.restore_all`
- Persist layout vía `scheduleSave()` post batch min/restore

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
- Certificado externo `FASE_83_APPROVED.md`
- Browser E2E
