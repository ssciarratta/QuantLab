# Fase 42 — Ops Metrics Panel

**Estado:** ✅ **APROBADO_INTERNO** (v0.34.0) — certificado externo `FASE_42_APPROVED.md` **NO** emitido  
**Base:** v0.33.0 · F41 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-086  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F42.md` · noche `INTERNAL_AUDIT_F19_F42_NIGHT.md`

## Objetivo
Exponer contadores in-process de `quantlab.infra.ops_metrics` en el workbench (API JSON + Prometheus text + panel UI) — sin flip LIVE.

## DoD
- [x] Reutilizar `ops_metrics` (snapshot + `render_prometheus_text`)
- [x] API `GET /api/ops/metrics` (JSON)
- [x] API opcional `GET /api/ops/prometheus` (text/plain)
- [x] UI: panel Ops Metrics (tabla counters + highlight `live_gate.blocked`)
- [x] Docs: `docs/FASE_42_OPS_METRICS.md` + IMPLEMENTATION_REPORT
- [x] Tests + QA
- [x] DEC-086 · bump **0.34.0**
- [x] Sin `FASE_42_APPROVED.md` · sin LIVE

## Contadores conocidos

| Counter | Origen |
|---------|--------|
| `live_gate.blocked` | `assert_live_routing_blocked()` / gate LIVE |
| `batch.failed_jobs` | batch runner fallos |
| `health.runs` | `run_health_checks()` |

Otros nombres se aceptan dinámicamente (registro in-process).

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/ops/metrics` | JSON: `counters`, `rows`, `live_gate_blocked`, highlight |
| GET | `/api/ops/prometheus` | `text/plain` Prometheus exposition |

Respuesta JSON: `ok`, `kind:ops_metrics`, `counters`, `rows`, `count`, `live_gate_blocked`, `highlight_live_gate_blocked`, `session_id`, `version`, `live_blocked`, `live_routing:false`, `research_safe:true`.

## UI

- Menú Inicio → Sistema → **Ops Metrics**
- Panel: tabla Counter / Value; fila `live_gate.blocked` resaltada si valor > 0
- Command palette `open.ops_metrics`

## Notas técnicas
- Módulo infra: `quantlab.infra.ops_metrics` (`OpsMetrics` thread-safe, proceso local)
- Handlers: `handle_get_ops_metrics` / `handle_get_ops_prometheus` en `workbench/api.py`
- No persiste counters a disco (in-process); reset al reiniciar proceso

## Fuera de alcance
LIVE · auth WAN · Electron · certificado externo `FASE_42_APPROVED.md` · browser E2E · scrape remoto Prometheus · persistencia histórica de counters
