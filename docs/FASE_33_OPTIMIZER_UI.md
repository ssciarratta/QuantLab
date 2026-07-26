# Fase 33 — Optimizer History + Pareto Panel

**Estado:** ✅ **APROBADO_INTERNO** (v0.25.0) — certificado externo `FASE_33_APPROVED.md` **NO** emitido  
**Base:** v0.24.0 · F32 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-077  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F33.md` · noche `INTERNAL_AUDIT_F19_F33_NIGHT.md`

## Objetivo
Tras un optimize lab run, persistir historial en session `optimizer/`, enriquecer POST con puntos Pareto (multi-objetivo simple sharpe↑/MDD↓) y exponer panel UI con historial + tabla + frente.

## DoD
- [x] Investigar `quantlab.optimizer` (grid, pareto)
- [x] Persist resultado en session `optimizer/<run_id>/`
- [x] `GET /api/lab/optimize/history` · POST `/api/lab/optimize` enriquecido
- [x] Panel Optimizer: historial + tabla + Pareto (texto/JSON + SVG opcional)
- [x] Docs: `docs/FASE_33_OPTIMIZER_UI.md` + IMPLEMENTATION_REPORT
- [x] Tests unitarios F33
- [x] DEC-077 · bump **0.25.0**

## Layout en disco

```text
<data/runtime/workbench>/<session_id>/
  optimizer/
    <run_id>/
      summary.json
```

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/lab/optimize/history` | lista corridas + latest |
| GET | `/api/lab/optimize/history/{run_id}` | summary persistido |
| POST | `/api/lab/optimize` | grid + métricas + Pareto + persist |

Parámetros POST: `lookbacks`, `quantities`, `n_bars` (8–60), `persist` (default true).

Respuesta incluye:
- `best` — params + score + metrics
- `history[]` — trial_id, params, score, metrics (sharpe, max_drawdown)
- `pareto` — frente no dominado (si ≥2 trials): objetivos sharpe max / MDD min

## UI

- Menú Laboratorio → **Optimizer**
- Inputs lookbacks / qty / n_bars → Optimizar
- Tabla resultados, puntos Pareto (+ scatter SVG simple), historial sesión

## Notas técnicas
- Reusa `GridSearchOptimizer.grid` + `pareto_from_trials` (F12)
- Persist solo sandbox de sesión (rechaza path externo)
- GET vacío = lista vacía (sin preview sintético costoso)

## Fuera de alcance
LIVE · auth WAN · Bayesian/Optuna · charting library · venue live
