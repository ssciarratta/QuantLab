# Fase 32 — Validation / Walk-Forward Runner UI

**Estado:** ✅ **APROBADO_INTERNO** (v0.24.0) — certificado externo `FASE_32_APPROVED.md` **NO** emitido  
**Base:** v0.23.0 · F31 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-076  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F32.md` · noche `INTERNAL_AUDIT_F19_F32_NIGHT.md`

## Objetivo
Runner UI de validación científica: train/val/OOS + walk-forward sobre serie sintética, con índices de segmentos, resumen anti-leakage, y persistencia en session `validation/`.

## DoD
- [x] Investigar `quantlab.validation` (splits, leakage, multiple_testing)
- [x] `POST /api/lab/validation/run` — splits + índices + anti-leakage; NO live
- [x] Persist resultado en session `validation/<run_id>/`
- [x] Panel Validation enriquecido (tablas + historial)
- [x] Docs: `docs/FASE_32_VALIDATION_UI.md` + IMPLEMENTATION_REPORT
- [x] Tests unitarios F32
- [x] DEC-076 · bump **0.24.0**

## Layout en disco

```text
<data/runtime/workbench>/<session_id>/
  validation/
    <run_id>/
      summary.json
```

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/lab/validation` | lista corridas + latest; preview efímero si vacío |
| GET | `/api/lab/validation/{run_id}` | summary persistido |
| POST | `/api/lab/validation/run` | genera splits + leakage + persist |

Parámetros POST: `n_bars` (20–200), `train_frac`/`val_frac`, `train_size`/`test_size`/`step`, `persist` (default true).

Respuesta incluye:
- `train_val_oos.segments` — índices start/end + timestamps
- `walk_forward.folds[].train_idx` / `test_idx`
- `anti_leakage` — checks train↔val, val↔oos, train↔oos, cada fold WF
- `multiple_testing` — métodos disponibles (info; no ajusta p-values aquí)

## UI

- Menú Laboratorio → **Validation Splits**
- Inputs n_bars / train / test → Correr splits
- Tablas anti-leakage, train/val/OOS, folds, historial sesión

## Notas técnicas
- Reusa `train_val_oos_split` / `walk_forward` / `check_temporal_leakage` (F10)
- Persist solo sandbox de sesión (rechaza path externo)
- GET vacío = preview sin escribir disco (compat F21)

## Fuera de alcance
LIVE · auth WAN · p-value adjustment UI · backtest OOS real · bars de venue live
