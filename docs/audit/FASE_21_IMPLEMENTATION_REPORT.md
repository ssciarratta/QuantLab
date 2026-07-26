# FASE 21 — Implementation Report (Lab Panels)

**Fecha:** 2026-07-26  
**Versión:** 0.13.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F20 Workbench v0.12.0  
**Alcance:** paneles + API lab — **sin chat**, **sin flip LIVE**  
**Audit INTERNAL:** `AUTO_AUDIT_2026-07-26_F21.md` · `FASE_21_REVIEW_PACKAGE.md` · `INTERNAL_AUDIT_F21.md` = **APROBADO_INTERNO**  
**Certificado externo:** NO (`FASE_21_APPROVED.md` no emitido)

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| L1 | Adapters thin lab | `workbench/lab_services.py` |
| L2 | Handlers `/api/lab/*` | `workbench/api.py` |
| L3 | Rutas HTTP | `workbench/server.py` |
| L4 | Paneles JS + menú | `static/js/panes/*`, `shell.js`, `index.html` |
| L5 | Cliente API lab | `static/js/api.js` |
| L6 | Suite unit | `tests/unit/workbench/test_lab_api.py` |
| L7 | Spec DoD | `docs/FASE_21_LAB_PANELS.md` |
| L8 | Bump | `pyproject.toml` + `__version__` → 0.13.0 |

## Mapeo a código existente

| Endpoint | Módulo real |
|----------|-------------|
| backtest | `BarBacktester` + `DummyStrategy` / `SimpleMomentumStrategy` / `BuyOnceStrategy` |
| scanner | `AlphaScanner` |
| experiments | `ExperimentRegistry` (tmp sesión) |
| optimize | `GridSearchOptimizer` |
| montecarlo | `MonteCarloSimulator` |
| features | `FeaturePipeline` + transformers |
| export-hb | `HummingbotExporter` |
| validation | `train_val_oos_split` / `walk_forward` |
| metrics | `WorkbenchState.last_lab_result` |

## Invariantes

- `LIVE_BLOCKED is True`
- Export `live_routing: false`; path externo → 400
- Sin credenciales / red para demos lab
- Bind loopback (F20)

## QA

```text
uv sync --extra dev
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench -q
uv run quantlab-health
```

## Fuera de alcance (correcto)

- Chat IA → F22  
- Flip `LIVE_BLOCKED`  
- Ordenes live / credenciales exchange
