# Residuos F10 / F12 / F14 — Implementation Report

**Fecha:** 2026-07-25  
**Versión:** 0.9.0  
**Estado:** código entregado + tests — no sustituye re-certificación de fases previas

---

## F10 — Corrección por múltiples comparaciones

| Método | API | Archivo |
|--------|-----|---------|
| Bonferroni | `bonferroni(p_values, alpha=0.05)` | `validation/multiple_testing.py` |
| Holm–Bonferroni | `holm_bonferroni(...)` | idem |
| Benjamini–Hochberg (FDR) | `benjamini_hochberg(...)` | idem |

Salida: `MultipleTestingResult(adjusted, rejected, method, alpha)`.

**Test:** `test_bonferroni_and_holm`

---

## F12 — Pareto multi-objetivo

| API | Archivo |
|-----|---------|
| `pareto_front(points, maximize=...)` | `optimizer/pareto.py` |
| `pareto_from_trials(trials, second_objective=...)` | idem |

Dominancia no-estricta; soporta mix maximize/minimize por objetivo.

**Tests:** `test_pareto_front_two_objectives`, `test_pareto_from_trials`

---

## F14 — Avellaneda–Stoikov MVP

| API | Archivo |
|-----|---------|
| `AvellanedaStoikovStrategy` | `research/strategies/avellaneda_stoikov.py` |
| `reservation_price(...)` / `optimal_half_spread(...)` | funciones puras |

Emite LIMIT bid/ask en replay 5B; **sin** routing LIVE.

**Test:** `test_avellaneda_formulas_and_quotes`

---

## LIVE (no residual de fase)

`assert_live_routing_blocked()` / `LiveOrderRouter` → siempre `ValidationError`.

---

## QA conjunto

Incluido en suite global **185 passed** (2026-07-25) junto a F17.
