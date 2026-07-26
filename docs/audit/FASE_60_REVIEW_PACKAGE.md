# FASE 60 — Review Package (i18n Scaffold)

**Fecha:** 2026-07-26  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Versión código (impl F60):** 0.52.0  
**LIVE_BLOCKED:** True  
**Certificado externo:** **NO** (`FASE_60_APPROVED.md` ausente)

## Resumen

Scaffold i18n del Workbench SPA: diccionario **es** (default) + stub **en**; `QLi18n.t()` aplicado en shell al load desde `settings.locale`; API `GET /api/i18n/{locale}` desde `static/i18n/*.json`. DEC-104 · bump 0.52.0.

## Lista A

| ID | Entrega | Evidencia |
|----|---------|-----------|
| A1 | i18n.js + JSON | `static/js/i18n.js` · `static/i18n/` |
| A2 | API i18n | `/api/i18n/{locale}` |
| A3 | Shell applyLocale | `shell.js` |
| A4 | data-i18n chrome/menú | `index.html` |
| A5 | Suite i18n | `test_i18n_f60.py` |
| A6 | DEC-104 | `learning/decisiones.txt` |
| A7 | Version 0.52.0 | `pyproject.toml` |

## Lista B (QA)

```
uv run quantlab-health                → ok=true, live_blocked=true, version=0.52.0
uv run python scripts/internal_audit_smoke.py
```

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_60_APPROVED.md`
- Default locale `es`
