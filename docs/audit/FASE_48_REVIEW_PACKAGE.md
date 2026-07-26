# FASE 48 — Review Package INTERNAL (Theme CSS Completion)

**Fecha:** 2026-07-26  
**Versión código (impl F48):** 0.40.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Impl SHA:** _(tip)_  
**LIVE:** BLOQUEADO  
**Certificado externo:** **NO** (`FASE_48_APPROVED.md` no emitido)

---

## Resumen ejecutivo

Completa el sistema de themes del workbench: tokens CSS para `slate` y `high-contrast` (chrome + semantic), `data-theme` en `documentElement` al load settings y al PUT `/api/settings`. DEC-092.

**Opción elegida:** extender variables CSS + cablear chrome a tokens; settings API ya existía (F36).

## Entregables

| ID | Entrega | Path |
|----|---------|------|
| A1 | Tokens CSS | `static/css/workbench.css` |
| A2 | data-theme apply | `index.html` · `shell.js` · `settings.js` |
| A3 | Spec | `docs/FASE_48_THEMES.md` |
| A4 | Implementation report | `docs/audit/FASE_48_IMPLEMENTATION_REPORT.md` |
| A5 | DEC-092 | `learning/decisiones.txt` |
| A6 | Version 0.40.0 | `pyproject.toml` |
| A7 | Suite F48 | `tests/unit/workbench/test_themes_f48.py` |
| A8 | Smoke F48 | `scripts/internal_audit_smoke.py` |
| A9 | Bundle to-phase 48 | `scripts/build_internal_review_bundle.py` |

## Evidencia QA

```
uv run mypy --strict src/quantlab     → Success: 175 files
uv run ruff check                     → All checks passed
uv run pytest -q                      → 846 passed
uv run quantlab-health                → ok=true, live_blocked=true, version=0.40.0
uv run python scripts/internal_audit_smoke.py → 34/34 PASS
```

## Smoke themes (síntesis)

| # | Check | Esperado |
|---|-------|----------|
| 1 | CSS tokens chrome | `--bg-banner` · `--bg-status` · `--bg-taskbar` |
| 2 | high-contrast block | `html[data-theme="high-contrast"]` |
| 3 | PUT theme=high-contrast | persist + GET roundtrip |
| 4 | PUT theme=slate | roundtrip back |
| 5 | applyTheme JS | `document.documentElement.setAttribute("data-theme"` |

## Fuera de alcance

LIVE · auth WAN · Electron · `FASE_48_APPROVED.md`

## Veredicto INTERNAL propuesto

**APROBADO_INTERNO** — ver `INTERNAL_AUDIT_F48.md`.
