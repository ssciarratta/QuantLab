# IMPLEMENTATION_PLAN.md — ML GBM (v4)

**Fecha:** 2026-08-12  
**Docs:** `AUDIT.md` + `DESIGN.md`  
**Código:** solo cuando el usuario autorice tras este plan.

---

## Orden

1. Skeleton `ml/` + schema features (sin entrenar)  
2. Dataset + labels desde `alpha_trials` (+ bootstrap fixture)  
3. Splits + train LightGBM + manifest  
4. Inferencia → `AlphaSignal ml_ranking`  
5. Registry + cableado lab opcional  
6. Tests + docs + restore tag post-ml

---

## IP-0 — Docs — HECHO
## IP-1 — Paquete ml/ + deps — HECHO
## IP-2 — features.py — HECHO
## IP-3 — dataset.py — HECHO
## IP-4 — splits.py — HECHO
## IP-5 — train.py + manifest — HECHO
## IP-6 — model.py + registry.py — HECHO
## IP-7 — Cableado lab include_ml — HECHO
## IP-8 — scripts/alpha_ml_bootstrap.py — HECHO
## IP-9 — HOWTO + RESUMEN — HECHO (tag post-ml al cerrar)

Implementado 2026-08-12.

---

## Criterios de cerrado

- [ ] Features solo desde señales normalizadas  
- [ ] Target = validated / DSR path, no retorno bruto  
- [ ] Manifest por entrenamiento  
- [ ] Inferencia = `ml_ranking` en contrato estándar  
- [ ] No modifica lógica scanners/pairwise  
- [ ] LIVE_BLOCKED intacto  
- [ ] Sin DL  

---

## No entra

SHAP completo (importance nativa LightGBM sí); multi-modelo ensemble; auto-retrain en UI cada minuto.
