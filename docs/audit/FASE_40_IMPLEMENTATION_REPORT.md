# FASE 40 — Implementation Report (Workspace Presets)

**Fecha:** 2026-07-26  
**Versión:** 0.32.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F39 Session ZIP · F28 Layout persistence  
**Alcance:** presets MDI → layout.json — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | Presets core | `workbench/presets.py` |
| A1 | `GET /api/presets` · `POST /api/presets/apply` | `api.py` + `server.py` |
| U1 | Menú Inicio → Espacios de trabajo | `static/index.html` · `shell.js` |
| U2 | API client + wm.closeAll | `static/js/api.js` · `wm.js` |
| T1 | Tests F40 | `tests/unit/workbench/test_presets_f40.py` |
| T2 | Smoke F40 | `scripts/internal_audit_smoke.py` |
| D2 | Spec + DEC-084 + bump | `docs/FASE_40_PRESETS.md` · `0.32.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Solo tres presets built-in (research / trading_paper / ops)
- Apply reemplaza `layout.json` (fail-closed ante nombre inválido)
- DEC-084

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_presets_f40.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Certificado externo `FASE_40_APPROVED.md`
- Presets custom / editables por usuario
