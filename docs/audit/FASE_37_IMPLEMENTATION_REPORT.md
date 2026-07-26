# FASE 37 — Implementation Report (First-run Onboarding Wizard)

**Fecha:** 2026-07-26  
**Versión:** 0.29.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F36 Settings · F22 Chat · F26 Paper Session · F19 Modes  
**Alcance:** wizard first-run + API onboarding — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| O1 | Persistencia onboarding | `workbench/onboarding.py` |
| O2 | Meta `onboarding_done` | `session.meta.json` |
| A1 | `GET /api/onboarding` · `POST /api/onboarding/complete` | `api.py` + `server.py` |
| U1 | Wizard modal JS | `static/js/onboarding.js` |
| U2 | Boot + CTAs | `shell.js` · `api.js` · `index.html` |
| U3 | CSS wizard | `static/css/workbench.css` |
| T1 | Tests F37 | `tests/unit/workbench/test_onboarding_f37.py` |
| T2 | Smoke F37 | `scripts/internal_audit_smoke.py` |
| D1 | Spec + DEC-081 + bump | `docs/FASE_37_ONBOARDING.md` · `0.29.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Wizard explica LIVE bloqueado; no ofrece flip
- Complete solo escribe meta (sin venue submit)
- DEC-081

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_onboarding_f37.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Certificado externo `FASE_37_APPROVED.md`
