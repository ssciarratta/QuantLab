# FASE 32 — Implementation Report (Validation / Walk-Forward Runner UI)

**Fecha:** 2026-07-26  
**Versión:** 0.24.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F31 Features UI · F21 Lab · F10 Validation  
**Alcance:** runner splits + anti-leakage + persist session — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| S1 | Persist validation runs | `workbench/validation_runs.py` |
| S2 | Session `validation_dir` | `workbench/session.py` |
| L1 | `run_lab_validation` índices + leakage + persist | `workbench/lab_services.py` |
| A1 | `GET /api/lab/validation` (+ `/{id}`) | `api.py` + `server.py` |
| A2 | `POST /api/lab/validation/run` | `api.py` + `server.py` |
| U1 | Panel Validation enriquecido | `static/js/panes/validation.js` |
| T1 | Tests F32 | `tests/unit/workbench/test_validation_f32.py` |
| D1 | Spec + DEC-076 + bump | `docs/FASE_32_VALIDATION_UI.md` · `0.24.0` |

## Invariantes

- `LIVE_BLOCKED is True`
- Persist solo sandbox sesión
- Path externo rechazado
- Nunca place_order venue
- DEC-076

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_validation_f32.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- UI de ajuste multiple-testing sobre p-values de estrategia
- Órdenes venue / auto-flip LIVE
