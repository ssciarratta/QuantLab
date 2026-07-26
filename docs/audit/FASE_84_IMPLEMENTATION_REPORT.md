# FASE 84 — Implementation Report (Cascade / Tile Windows)

**Fecha:** 2026-07-26  
**Versión:** 0.76.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F83 Minimize / Restore All v0.75  
**Impl SHA:** `PENDING`  
**Alcance:** Cascade / Tile windows — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | `cascadeWindows` / `tileWindows` + pure rects + persist | `static/js/wm.js` |
| D2 | Python mirror | `workbench/window_layout.py` |
| D3 | Commands registry | `workbench/commands.py` |
| D4 | Palette + menú Inicio + i18n | `command_palette.js` · `shell.js` · `index.html` · `i18n.js` |
| D5 | Spec + DEC-128 + bump | `docs/FASE_84_CASCADE_TILE.md` · **0.76.0** |
| D6 | Suite | `tests/unit/workbench/test_cascade_tile_f84.py` |
| D7 | Smoke F84 | `scripts/internal_audit_smoke.py` |
| D8 | Implementation report | este doc |
| D9 | Bundle default F19–F84 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_84_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-128
- `phases_summary == "F19–F84 INTERNAL"`
- About `version` ≡ `__version__` · **0.76.0**
- Commands API incluye `action.cascade_windows` + `action.tile_windows`
- Persist layout vía `scheduleSave()` post cascade/tile

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
- Certificado externo `FASE_84_APPROVED.md`
- Browser E2E
