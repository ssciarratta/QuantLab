# FASE 24 — Implementation Report (Venue plugins + MD read-only)

**Fecha:** 2026-07-26  
**Versión:** 0.16.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F23 Paper Book v0.15.0  
**Alcance:** Entry-point plugins + A3 MD env opt-in + generic CSV/REST — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| P1 | Entry-point loader | `brokers/plugins.py` |
| P2 | Registry + plugins + generics | `brokers/registry.py` |
| P3 | A3 MD resolve fake\|env | `brokers/a3/md_backend.py` + `adapter_port.py` |
| P4 | Generic CSV MD | `brokers/generic/csv_md.py` |
| P5 | Generic REST skeleton | `brokers/generic/rest_skeleton.py` |
| P6 | Workbench md_provider | `workbench/api.py` + Market UI |
| P7 | Tests | `tests/unit/brokers/test_plugins.py`, `test_a3_md_readonly_fallback.py`, `test_generic_rest_csv.py`, `tests/unit/workbench/test_api_md_provider.py` |
| P8 | Ops docs | `docs/ops/BROKER_PLUGINS.md` |
| P9 | Spec DoD | `docs/FASE_24_VENUE_MD_PLUGINS.md` |
| P10 | Bump | `pyproject.toml` + `__version__` → 0.16.0 |

## Invariantes

- `LIVE_BLOCKED is True`
- A3 / generic_csv / generic_rest: `submit`/`cancel` → `assert_live_routing_blocked`
- `md_source=env` sin flag/creds → FakeA3Backend + health fallback detail
- Plugins fallidos: structlog warning, proceso no crashea
- Plugins **no** sombrean venues ya registrados (audit H1)

## Remediación audit INTERNAL

| ID | Fix |
|----|-----|
| H1 | `has_venue` + refuse shadow en loader/`register(from_plugin=True)` + `test_plugin_cannot_shadow_builtin` |

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/brokers tests/unit/workbench
uv run ruff check src/quantlab tests/unit/brokers tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/brokers tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Órdenes venue / LIVE
- Ops Desk launcher (F25)
