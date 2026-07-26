# Fase 50 — Performance Baseline Workbench API

**Estado:** ✅ **APROBADO_INTERNO** (v0.42.0) — certificado externo `FASE_50_APPROVED.md` **NO** emitido  
**Base:** v0.41.0 · F49 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-094  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F50.md` · noche `INTERNAL_AUDIT_F19_F50_NIGHT.md`

## Objetivo

Establecer un baseline de latencia local (loopback) para endpoints clave del workbench API, con assert de p95/max bajo umbral razonable (500ms), sin flip LIVE.

## DoD

- [x] Módulo `quantlab.workbench.perf_baseline` (medición + reporte)
- [x] Suite `tests/unit/workbench/test_perf_baseline_f50.py`
- [x] CLI opcional `scripts/workbench_perf_baseline.py`
- [x] Docs: `docs/FASE_50_PERF_BASELINE.md` + IMPLEMENTATION_REPORT (con números)
- [x] Smoke F50 + bundle default F19–F50
- [x] DEC-094 · bump **0.42.0**
- [x] Sin `FASE_50_APPROVED.md` · sin LIVE
- [x] Si algo absurdo de lento → fix rápido (no requerido: latencias ≪ 500ms)

## Endpoints medidos

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/health` | Incluye smoke paper ledger local (más caro) |
| GET | `/api/mode` | Lectura de modo in-process |
| GET | `/api/commands` | Command palette JSON |
| GET | `/api/about` | Version + phases + bind policy |
| GET | `/api/lab/capabilities` | Catálogo lab research-safe |

## Umbral

- **p95 < 500ms** y **max < 500ms** por endpoint (loopback local).
- Samples default: 25 (+ 3 warmup).
- Servidor: `ThreadingHTTPServer` en thread daemon, `127.0.0.1:0`.

## Uso

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_perf_baseline_f50.py
uv run python scripts/workbench_perf_baseline.py
uv run python scripts/workbench_perf_baseline.py --json --out /tmp/perf_f50.json
```

## Fuera de alcance

LIVE · auth WAN · Electron · browser E2E · carga concurrente · certificado externo `FASE_50_APPROVED.md` · profiling profundo / APM
