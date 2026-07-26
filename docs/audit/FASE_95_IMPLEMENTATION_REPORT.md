# FASE 95 — Implementation Report

**Fase:** F95 Diagnostics Snapshot Panel (read-only)
**Versión:** 0.87.0 · **DEC:** DEC-139 · **Fecha:** 2026-07-26
**Branch:** `cursor/modo-real-workbench-aafd` · **LIVE_BLOCKED:** True
**Estado:** implementada · cierre formal pendiente de auditoría (sin `FASE_95_APPROVED.md`)

---

## 1. Entregables (Lista A)

| ID | Artefacto | Path |
|---|---|---|
| A1 | Endpoint | `src/quantlab/workbench/api.py` (`handle_get_diagnostics`) |
| A2 | Ruta HTTP | `src/quantlab/workbench/server.py` (`/api/diagnostics`) |
| A3 | Catálogo | `src/quantlab/workbench/api_catalog.py` |
| A4 | Pane UI | `src/quantlab/workbench/static/js/panes/diagnostics.js` |
| A5 | Wiring | `api.js` · `shell.js` · `index.html` · `commands.py` · i18n |
| A6 | Tests | `tests/unit/workbench/test_diagnostics_f95.py` |
| A7 | Smoke F95 | `scripts/internal_audit_smoke.py` |
| A8 | Spec + DEC-139 | `docs/FASE_95_DIAGNOSTICS.md` · `learning/decisiones.txt` |

## 2. Diseño

- `handle_get_diagnostics` compone estado en memoria + `run_health_checks()`
  (resumido a ok/total) + `check_paper_reconciliation()` (read-only). No abre
  ni escribe archivos de journal/book.
- Pane con única llamada `QLApi.diagnostics()`; botón copiar usa clipboard del
  navegador. Test de DoD garantiza ausencia de verbos mutantes.

## 3. QA (2026-07-26, Windows)

| Gate | Resultado |
|---|---|
| `uv run mypy --strict src/quantlab` | Success: no issues (200 files) |
| `uv run ruff check src/quantlab tests scripts` | All checks passed |
| `uv run pytest -q` | 1189 passed, 2 skipped |
| `uv run python scripts/internal_audit_smoke.py` | PASS (incluye F95) |

## 4. Invariantes

- `LIVE_BLOCKED is True`; `live_routing=false`; endpoint sin acciones.
- Catálogo OpenAPI sin rutas LIVE (guard F55 intacto).
- No se emitió `FASE_95_APPROVED.md`.
