# Fase 29 — Report Viewer + Metrics History

**Estado:** ✅ **APROBADO_INTERNO** (v0.21.0) — certificado externo `FASE_29_APPROVED.md` **NO** emitido  
**Base:** v0.20.0 · F28 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-073  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F29.md` · noche `INTERNAL_AUDIT_F19_F29_NIGHT.md`

## Objetivo
Tras un backtest lab exitoso, persistir `MetricsResult`/summary (JSON + HTML vía `ReportGenerator`) en la sesión durable (`reports/`) y exponer listado + preview en el workbench.

## DoD
- [x] Persistencia en session `reports/` vía `workbench/reports.py` + `ReportGenerator`
- [x] API: `GET /api/lab/reports`, `GET /api/lab/reports/{id}` (POST implícito en `/api/lab/backtest`)
- [x] Panel UI Reports: lista + preview HTML o JSON formateado
- [x] Docs: `docs/FASE_29_REPORTS.md` + IMPLEMENTATION_REPORT
- [x] Tests unitarios F29
- [x] DEC-073 · bump **0.21.0**

## Layout en disco

```text
<data/runtime/workbench>/<session_id>/reports/
  <report_id>/
    summary.json              # MetricsResult + summary lab + meta
    report_default_v1.html    # ReportGenerator (si viable)
```

- `report_id` = `{experiment_id}-{UTC stamp}` (charset `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`)
- Escritura atómica de `summary.json`
- Path sandbox: report fuera de `reports/` → `ValidationError`

## API

| Método | Path | Notas |
|--------|------|-------|
| POST | `/api/lab/backtest` | Persiste report; respuesta incluye `report_id` |
| GET | `/api/lab/reports` | Lista (reciente primero) |
| GET | `/api/lab/reports/{id}` | Summary + `html` (si existe) |

## UI

- Menú Laboratorio → **Reports**
- Lista clickeable; preview JSON (`pre`) o HTML (`iframe` sandbox + `srcdoc`)

## Notas técnicas
- Sin flip LIVE · sin place_order venue
- HTML best-effort: si `ReportGenerator` falla, queda JSON mínimo
- `metrics_result.experiment_id` conserva el id del backtest; el folder usa `report_id`

## Fuera de alcance
LIVE · auth WAN · reports de scanner/optimize/MC · diff/compare UI multi-report
