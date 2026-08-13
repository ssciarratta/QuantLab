# IMPLEMENTATION_PLAN.md — Pipeline Alpha v3

**Fecha:** 2026-08-12  
**Docs:** `AUDIT.md` + `DESIGN.md`  
**Regla:** un paso chico → criterio de verificación → luego el siguiente. Sin código hasta completar este plan (este archivo **es** el plan; la implementación empieza en IP-1 cuando el usuario autorice).

---

## Orden de prioridad

1. Separación rankings + ledger (causa raíz)  
2. Contrato individual → `AlphaSignal`  
3. `validate_candidate` único  
4. Cablear UI/API mínimo  
5. Deprecar semántica de pipeline/strategy_rank como “validado”

---

## IP-0 — Freeze docs (hecho con este archivo)

- [x] AUDIT.md (6 puntos)  
- [x] DESIGN.md  
- [x] Este plan  

**Verificación:** archivos en `docs/scanner/pipeline/`.

---

## IP-1 — Ledger persistente de trials de validación — HECHO

## IP-2 — Hard gate anti-leakage en scanner individual — HECHO

## IP-3 — Individual → `AlphaSignal` + percentil — HECHO

## IP-4 — `validate_candidate` único — HECHO

## IP-5 — Ranking B (estrategias validadas) — HECHO

## IP-6 — Cablear pairwise validation al ledger persistente — HECHO

## IP-7 — Pipeline Binance usa validate_candidate — HECHO

## IP-8 — Etiquetar strategy_rank como exploración — HECHO

## IP-9 — UI mínima Scanner — HECHO

## IP-10 — Docs operativos + RESUMEN — HECHO

Ver `HOWTO.md`. Implementado 2026-08-12.

---

## Criterios globales de “cerrado”

- [ ] Ranking A nunca contiene métricas de backtest.  
- [ ] Toda validación pasa por `validate_candidate` + ledger disco.  
- [ ] Individual y par comparten contrato `AlphaSignal` + mismo path de validación.  
- [x] Ranking B muestra todas las validaciones (aprobadas / rechazadas / fallidas).  
- [ ] Pairwise detectors sin cambios de lógica.  
- [ ] `LIVE_BLOCKED` intacto.  
- [ ] Tests verdes mypy/ruff en módulos tocados.

---

## Qué no entra en ninguna IP

Nuevas features, meta-score individual+par, más parámetros de WF en UI, LIVE, scipy ADF, rediseño Kronos.
