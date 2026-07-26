# FASE 96 — Implementation Report

**Fase:** F96 Diagnostics Download (support snapshot)
**Versión:** 0.88.0 · **DEC:** DEC-140 · **Fecha:** 2026-07-26
**Branch:** `cursor/modo-real-workbench-aafd` · **LIVE_BLOCKED:** True
**Estado:** implementada · cierre formal pendiente de auditoría (sin `FASE_96_APPROVED.md`)

---

## 1. Entregables (Lista A)

| ID | Artefacto | Path |
|---|---|---|
| A1 | Handler descarga | `src/quantlab/workbench/api.py` (`handle_get_diagnostics_download`) |
| A2 | Ruta HTTP | `src/quantlab/workbench/server.py` (`/api/diagnostics.json`) |
| A3 | Catálogo | `src/quantlab/workbench/api_catalog.py` |
| A4 | UI botón + helper | `panes/diagnostics.js` · `api.js` |
| A5 | Tests | `tests/unit/workbench/test_diagnostics_download_f96.py` |
| A6 | Smoke F96 | `scripts/internal_audit_smoke.py` |
| A7 | Spec + DEC-140 | `docs/FASE_96_DIAGNOSTICS_DOWNLOAD.md` · `learning/decisiones.txt` |

## 2. Diseño

- Reutiliza `handle_get_diagnostics` (F95) y serializa a JSON adjunto con
  `_send_download`, siguiendo el patrón de `fills.csv` (F65). Sin nuevas fuentes
  de datos ni mutaciones. Nombre de archivo saneado por `session_id`.

## 3. QA (2026-07-26, Windows)

| Gate | Resultado |
|---|---|
| `uv run mypy --strict src/quantlab` | Success: no issues (200 files) |
| `uv run ruff check src/quantlab tests scripts` | All checks passed |
| `uv run pytest -q` | 1194 passed, 2 skipped |
| `uv run python scripts/internal_audit_smoke.py` | PASS (incluye F96) |

## 4. Invariantes

- `LIVE_BLOCKED is True`; descarga sin acciones ni mutaciones.
- Catálogo OpenAPI sin rutas LIVE (guard F55 intacto).
- No se emitió `FASE_96_APPROVED.md`.
