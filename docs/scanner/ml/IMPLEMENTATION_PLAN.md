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

## IP-0 — Docs (este entregable)

- [x] AUDIT.md  
- [x] DESIGN.md  
- [x] Plan  

**Verificación:** `docs/scanner/ml/`

---

## IP-1 — Paquete `research/alpha/ml/` + deps

**Qué:** Crear módulo vacío con `__init__.py`; añadir `lightgbm` (optional extra `ml` en pyproject si se quiere no forzar a todos).  
**Verificación:** `import quantlab.research.alpha.ml` ; CI sin extra sigue verde.

---

## IP-2 — `features.py`

**Qué:** `signal_to_feature_row(AlphaSignal | dict) -> dict[str, float|str|None]` según DESIGN §3; `feature_schema_version`.  
**Verificación:** test con signal individual + pair fixture; keys estables; no lee barras.

---

## IP-3 — `dataset.py` + labels

**Qué:** Construir filas join scan features ↔ trial outcome; fixture sintético con N≥50 para tests.  
**Verificación:** test dataset tiene columnas X + `y` binaria; rechaza retorno bruto como target.

---

## IP-4 — `splits.py`

**Qué:** Walk-forward tabular + purge/embargo por horizonte.  
**Verificación:** ningún timestamp de test en train; gap ≥ H.

---

## IP-5 — `train.py` + manifest

**Qué:** Fit LightGBM binary; guardar artefacto + `experiments/alpha_ml/{id}/manifest.json` + metrics (AUC, importance). Abort si N_pos < umbral.  
**Verificación:** train sobre fixture → archivos en tmp_path; manifest con commit/schema/hyperparams.

---

## IP-6 — `model.py` + `registry.py`

**Qué:** Cargar modelo activo; `score_candidates` → `tuple[AlphaSignal]` `ml_ranking`; registry inactive → lista vacía / warning.  
**Verificación:** test inferencia sin red; scores en [0,1]; contrato AlphaSignal.

---

## IP-7 — Cableado lab (mínimo)

**Qué:** Flag en pairwise/individual scanner o post-paso: si registry activo, append señales ML al payload Ranking A. Default **off**.  
**No:** cambiar detectores.  
**Verificación:** con modelo inactive, payload idéntico; con active + mock, aparecen `ml_ranking`.

---

## IP-8 — Script bootstrap labels (opcional pero recomendado)

**Qué:** CLI/research script: replay scans históricos → `validate_candidate` → llenar `alpha_trials` para tener N real.  
**Verificación:** dry-run documentado; no LIVE.

---

## IP-9 — Docs usuario + RESUMEN + tag `restore/post-ml-gbm-…`

**Qué:** HOWTO 1 página; actualizar RESUMEN.  
**Verificación:** checklist DESIGN §5 reflejado.

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
