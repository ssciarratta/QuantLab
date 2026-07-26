# FASE 45 — Implementation Report (About Dialog + Version Badge)

**Fecha:** 2026-07-26  
**Versión:** 0.37.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F44 E2E Paper Workflow Integration  
**Impl SHA:** `a103236`  
**Alcance:** About API + badge + diálogo — **sin flip LIVE** · **sin browser**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| T1 | About module + API | `workbench/about.py` · `api.py` · `server.py` |
| T2 | UI badge + dialog | `static/js/about.js` · `shell.js` · `index.html` · CSS |
| T3 | Command `open.about` | `workbench/commands.py` |
| T4 | Suite F45 | `tests/unit/workbench/test_about_f45.py` |
| T5 | Smoke F45 | `scripts/internal_audit_smoke.py` |
| D1 | Spec + DEC-089 + bump | `docs/FASE_45_ABOUT.md` · `0.37.0` |
| D2 | Implementation report | este doc |
| D3 | Bundle default to-phase 45 | `scripts/build_internal_review_bundle.py` |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_45_APPROVED.md`
- Sin flip LIVE / place_order venue
- Sin browser / Playwright
- DEC-089
- `phases_summary == "F19–F45 INTERNAL"`

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_about_f45.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Certificado externo `FASE_45_APPROVED.md`
