# Fase 31 — Feature Store Browser + Pipeline Runner UI

**Estado:** ✅ **APROBADO_INTERNO** (v0.23.0) — certificado externo `FASE_31_APPROVED.md` **NO** emitido  
**Base:** v0.22.0 · F30 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-075  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F31.md` · noche `INTERNAL_AUDIT_F19_F31_NIGHT.md`

## Objetivo
Browser read-only del Feature Store (session `features/` o store default) + runner UI del pipeline demo que **persiste** frames vía `quantlab.features.store.FeatureStore`.

## DoD
- [x] Investigar `quantlab.features` (store, pipeline, transformers) — APIs read-only + demo run
- [x] `GET /api/lab/features/store` — listar artifacts (session/features o default)
- [x] `POST /api/lab/features/run` — pipeline demo + persist en sesión (alias `POST /api/lab/features`)
- [x] Panel Features enriquecido: listar store + correr pipeline + ver columnas
- [x] Docs: `docs/FASE_31_FEATURES_UI.md` + IMPLEMENTATION_REPORT
- [x] Tests unitarios F31
- [x] DEC-075 · bump **0.23.0**

## Layout en disco

```text
<data/runtime/workbench>/<session_id>/
  features/                         # FeatureStore root (hashed_segments_v1)
    <instrument__hash>/
      <pipeline__hash>/
        <version__hash>/
          frame.json
          meta.json
```

Default global (opcional, si no hay sesión):

```text
data/features/                      # candidato default
# o QUANTLAB_FEATURE_STORE_PATH=<path>
```

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/lab/features/store` | artifacts + columns_union; vacío ok |
| POST | `/api/lab/features/run` | demo pipeline + `FeatureStore.put` en session |
| POST | `/api/lab/features` | alias legacy → mismo handler |

Pipeline demo: `close_price` + `simple_return` + `log_return` (`wb_demo_pipeline`).

## UI

- Menú Laboratorio → **Features**
- Correr pipeline → persiste + refresca store
- Tabla artifacts (instrument / pipeline / version / columns / bars)
- Sección columnas (union o del último run)

## Notas técnicas
- Reusa `FeatureStore` / `FeaturePipeline` / transformers oficiales (F5)
- Persist solo en sandbox de sesión (rechaza `store_root`/`path` externo)
- Versión demo auto: `wb-demo-<UTC stamp>` (idempotencia por checksum del store)

## Fuera de alcance
LIVE · auth WAN · delete/overwrite store · transformers custom UI · S3/remoto (TD-09)
