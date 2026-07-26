# FASE 93 — Implementation Report

**Fase:** F93 Venues / Broker Registry Panel (read-only)
**Versión:** 0.85.0 · **DEC:** DEC-137 · **Fecha:** 2026-07-26
**Branch:** `cursor/modo-real-workbench-aafd` · **LIVE_BLOCKED:** True
**Estado:** **APROBADO_INTERNO** (`INTERNAL_AUDIT_F93.md`) · cierre externo pendiente (sin `FASE_93_APPROVED.md`)

---

## 1. Entregables (Lista A)

| ID | Artefacto | Path |
|---|---|---|
| A1 | API enriquecida | `src/quantlab/workbench/api.py` (`handle_get_venues`) |
| A2 | Pane UI | `src/quantlab/workbench/static/js/panes/venues.js` |
| A3 | Wiring shell/index/commands | `shell.js` · `index.html` · `commands.py` |
| A4 | i18n | `static/i18n/es.json` · `en.json` · `js/i18n.js` |
| A5 | Tests | `tests/unit/workbench/test_venues_panel_f93.py` |
| A6 | Smoke F93 | `scripts/internal_audit_smoke.py` |
| A7 | Spec | `docs/FASE_93_VENUES_PANEL.md` |
| A8 | DEC-137 + bump | `learning/decisiones.txt` · `pyproject.toml` |

## 2. Diseño

- Sin rutas nuevas: se enriquece `GET /api/venues` con estado de conexión y
  el contrato de plugins v1 (`BROKER_PLUGIN_API_VERSION`,
  `BROKER_PLUGIN_CAPABILITIES`, wrapper `ReadOnlyBrokerPort`, ejecución
  bloqueada). Payload derivado solo de estado en memoria; no toca disco.
- El pane consume únicamente `QLApi.venues()`; el test de DoD verifica que no
  existan otras llamadas ni verbos mutantes en el JS.

## 3. QA (2026-07-26, Windows)

| Gate | Resultado |
|---|---|
| `uv run mypy --strict src/quantlab` | Success: no issues (200 files) |
| `uv run ruff check src/quantlab tests scripts` | All checks passed |
| `uv run pytest -q` | 1177 passed, 2 skipped |
| `uv run python scripts/internal_audit_smoke.py` | PASS (incluye F93) |

## 4. Invariantes

- `LIVE_BLOCKED is True`; panel sin ninguna acción de ejecución/conexión.
- Plugins externos siempre detrás de `ReadOnlyBrokerPort` (F24/F87, sin cambio).
- No se emitió `FASE_93_APPROVED.md`.
