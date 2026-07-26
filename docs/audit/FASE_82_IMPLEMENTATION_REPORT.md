# FASE 82 — Implementation Report (Window Snap to Edges)

**Fecha:** 2026-07-26  
**Versión:** 0.74.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F81 Custom Preset Delete v0.73  
**Impl SHA:** _(tip feat commit)_  
**Alcance:** Snap bordes viewport al soltar drag — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | `snapPosition` + drag release | `static/js/wm.js` |
| D2 | Espejo Python | `workbench/snap_position.py` |
| D3 | Spec + DEC-126 + bump | `docs/FASE_82_WINDOW_SNAP.md` · **0.74.0** |
| D4 | Suite | `tests/unit/workbench/test_window_snap_f82.py` |
| D5 | Smoke F82 | `scripts/internal_audit_smoke.py` |
| D6 | Implementation report | este doc |
| D7 | Bundle default F19–F82 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_82_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-126
- `phases_summary == "F19–F82 INTERNAL"`
- About `version` ≡ `__version__` · **0.74.0**
- Threshold default **12px**
- Persist layout vía `scheduleSave()` post-snap

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
- Certificado externo `FASE_82_APPROVED.md`
- Snap entre ventanas / midlines
