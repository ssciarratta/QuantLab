# FASE 85 — Implementation Report (Bring to Front / Send to Back)

**Fecha:** 2026-07-26  
**Versión:** 0.77.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F84 Cascade / Tile Windows v0.76  
**Impl SHA:** `PENDING`  
**Alcance:** Bring to Front / Send to Back (z-order) — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | `bringToFront` / `sendToBack` + context menu + dblclick | `static/js/wm.js` |
| D2 | Restore `z` on open + `mergeOpts` | `wm.js` · `shell.js` |
| D3 | Commands registry | `workbench/commands.py` |
| D4 | Palette + menú Inicio + i18n + CSS | `command_palette.js` · `shell.js` · `index.html` · `i18n.js` · `workbench.css` |
| D5 | Spec + DEC-129 + bump | `docs/FASE_85_ZORDER.md` · **0.77.0** |
| D6 | Suite | `tests/unit/workbench/test_zorder_f85.py` |
| D7 | Smoke F85 | `scripts/internal_audit_smoke.py` |
| D8 | Implementation report | este doc |
| D9 | Bundle default F19–F85 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_85_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-129
- `phases_summary == "F19–F85 INTERNAL"`
- About `version` ≡ `__version__` · **0.77.0**
- Commands API incluye `action.bring_to_front` + `action.send_to_back`
- Persist `z` vía `scheduleSave()` post bring/send

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
- Certificado externo `FASE_85_APPROVED.md`
- Browser E2E
