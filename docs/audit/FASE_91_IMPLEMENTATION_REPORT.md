# FASE 91 — Implementation Report (Paper Session Rehydrate post-rebuild)

Fecha: 2026-07-26  
Versión: 0.83.0  
Branch: `cursor/modo-real-workbench-aafd`  
Prereq: F88 (reconciliation core) · F90 (panel UI)  
Alcance: rehydrate explícito del runtime — **sin flip LIVE**

## Entregas

| ID | Entrega | Evidencia |
|---|---|---|
| D1 | `WorkbenchState.rehydrate_session()` (reusa `switch_session`) | `workbench/api.py` |
| D2 | `handle_post_paper_rehydrate` + activity `rehydrate` | `workbench/api.py` · `activity.py` |
| D3 | Ruta `POST /api/paper/reconciliation/rehydrate` | `workbench/server.py` |
| D4 | Catálogo OpenAPI POST-only | `workbench/api_catalog.py` |
| D5 | Botón panel Reconciliación con `confirm()` | `static/js/panes/reconciliation.js` |
| D6 | `QLApi.paperRehydrate()` | `static/js/api.js` |
| D7 | Suite e2e drift→rebuild→rehydrate + fail-closed | `tests/unit/workbench/test_paper_rehydrate_f91.py` |
| D8 | Smoke F91 + bundle to-phase 91 | `scripts/internal_audit_smoke.py` · `build_internal_review_bundle.py` |
| D9 | Spec + DEC-135 + bump | `docs/FASE_91_PAPER_REHYDRATE.md` · **0.83.0** |

## Política adoptada

Rehydrate = reinicio de proceso en miniatura: teardown del runner paper y del
broker, relectura del estado durable, recomputo de la reconciliación. No hay
auto-recuperación: si el durable sigue inválido, el estado queda bloqueado
igual que al boot. El único camino que reconstruye archivos sigue siendo el
CLI offline con backup (F88).

## QA

```text
ruff check src/quantlab tests scripts    PASS
mypy --strict src/quantlab               PASS (200 source files)
pytest -q                                1171 passed, 2 skipped
internal_audit_smoke.py                  PASS (incluye F91)
```

No existe ni se debe crear `FASE_91_APPROVED.md`.
