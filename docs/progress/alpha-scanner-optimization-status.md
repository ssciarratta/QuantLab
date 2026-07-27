# Alpha Scanner optimization — status

**Actualizado:** 2026-07-27  
**Fase actual:** FASE 4 — Scoring **COMPLETA**  
**Siguiente:** FASE 5 — Perfiles (momentum / MR / MM / AS / funding / balanced)

---

## FASE 0–3 — hecho

Scoring default lab: `AlphaScanner` / `legacy_v1` (sin cambio).

## FASE 4 — hecho

| Ítem | Estado |
|------|--------|
| `min_max_normalize` / `robust_normalize` | OK |
| `CompositeScorer` + `FactorSpec` | OK |
| `PenaltyEngine` (missing + quality) | OK |
| Missing policies (exclude / renormalize / penalize / fallback) | OK |
| Componentes con weight/contrib | OK |
| Parity scorer ↔ AlphaScanner (min-max, sin penalties) | OK |
| Default lab cambia de fórmula | **No** |

### Archivos

- `src/quantlab/research/alpha/scoring.py`
- `tests/unit/research/test_alpha_scoring_f4.py`

### Limitaciones

- Robust norm aún no es default.
- Quality penalties opt-in (`apply_quality_penalties=False` por defecto).

---

## Fases

| Fase | Estado |
|------|--------|
| 0 Discovery | **DONE** |
| 1 Contratos | **DONE** |
| 2 Universo/calidad | **DONE** |
| 3 Features | **DONE** |
| 4 Scoring | **DONE** |
| 5 Perfiles | PENDING |
| 6–10 | PENDING |
