# Fase 34 — Monte Carlo History + Hummingbot Export Wizard

**Estado:** ✅ **APROBADO_INTERNO** (v0.26.0) — certificado externo `FASE_34_APPROVED.md` **NO** emitido  
**Base:** v0.25.0 · F33 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-078  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F34.md` · noche `INTERNAL_AUDIT_F19_F34_NIGHT.md`

## Objetivo
Persistir historial de Monte Carlo en session `montecarlo/`, enriquecer panel con intervalos CI, y wizard de export Hummingbot (lista experiments → validate/build/export path-safe) con listado de exports previos y banner `live_routing:false`.

## DoD
- [x] Persist MC runs en session `montecarlo/<run_id>/`
- [x] `GET /api/lab/montecarlo/history` · POST `/api/lab/montecarlo` enriquecido
- [x] Panel MC: historial + intervalos CI
- [x] Export HB wizard: experiments + validate/build/export + banner
- [x] `GET /api/lab/exports` lista exports previos
- [x] Docs: `docs/FASE_34_MC_EXPORT.md` + IMPLEMENTATION_REPORT
- [x] Tests unitarios F34
- [x] DEC-078 · bump **0.26.0**

## Layout en disco

```text
<data/runtime/workbench>/<session_id>/
  montecarlo/
    <run_id>/
      summary.json
  exports/
    <experiment_id>.json          # alias latest
    hb-<stamp>-<experiment_id>.json  # snapshot histórico
```

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/lab/montecarlo/history` | lista corridas + latest |
| GET | `/api/lab/montecarlo/history/{run_id}` | summary persistido |
| POST | `/api/lab/montecarlo` | mini MC + CI + persist |
| GET | `/api/lab/exports` | lista exports HB sesión |
| GET | `/api/lab/exports/{export_id}` | payload de un export |
| POST | `/api/lab/export-hb` | validate → build → export |

Parámetros POST montecarlo: `n_scenarios` (2–20), `n_bars` (8–60), `noise_bps`, `persist` (default true).

Respuesta MC incluye: `mean_equity`, `std_equity`, `ci_low`, `ci_high`, `ci_level=0.95`, `final_equities`.

Export respuesta incluye: `steps.{validate,build,export}`, `banner`, `live_routing:false`, `export_id`, `path` + `latest_path`.

## UI

- Menú Laboratorio → **Monte Carlo** — historial + CI bar
- Menú Laboratorio → **Hummingbot Export** — wizard (select experiment, banner live_routing:false, exports previos)

## Notas técnicas
- Reusa `MonteCarloSimulator` (F11) + `HummingbotExporter` (F16)
- Persist solo sandbox de sesión (rechaza path externo)
- GET vacío = lista vacía (sin preview sintético costoso)

## Fuera de alcance
LIVE · auth WAN · order routing HB real · certificado externo `FASE_34_APPROVED.md`
