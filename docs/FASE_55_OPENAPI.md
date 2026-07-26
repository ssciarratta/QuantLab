# Fase 55 — OpenAPI / API Catalog

**Estado:** ✅ **APROBADO_INTERNO** (v0.47.0) — certificado externo `FASE_55_APPROVED.md` **NO** emitido  
**Base:** v0.46.0 · F54 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-099  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F55.md` · noche `INTERNAL_AUDIT_F19_F55_NIGHT.md`

## Objetivo

Exponer un catálogo HTTP machine-readable de la API del workbench:

- **OpenAPI 3 mínimo** generado desde un catálogo estático de rutas (paths / methods / summary).
- **Sin FastAPI** — el workbench sigue en stdlib `http.server`.
- **Research-safe** — sin rutas de LIVE trading.

## DoD

- [x] `GET /api/openapi.json` — schema OpenAPI 3.0.x
- [x] Módulo `quantlab.workbench.api_catalog` con rutas documentadas
- [x] Schema incluye `/api/health` y `/api/livez`; **no** live trading routes
- [x] Link About → API (OpenAPI) opcional
- [x] Spec + IMPLEMENTATION_REPORT
- [x] Suite `tests/unit/workbench/test_openapi_f55.py`
- [x] Smoke F55 + bundle default F19–F55
- [x] DEC-099 · bump **0.47.0**
- [x] Sin `FASE_55_APPROVED.md` · sin LIVE

## Diseño

| Artefacto | Rol |
|-----------|-----|
| `api_catalog.API_ROUTES` | Catálogo canónico (path, method, summary, tags) |
| `build_openapi_schema()` | Documento OpenAPI 3 mínimo (paths + info + x-quantlab) |
| `GET /api/openapi.json` | Handler HTTP que devuelve el schema |

### Invariantes del catálogo

1. Debe documentar `GET /api/health` y `GET /api/livez`.
2. No documenta `/api/live` ni `/api/live/*` (≠ `/api/livez`).
3. No documenta place_order venue / set_live / flip_live.
4. `x-quantlab.live_blocked == true` · `live_routing == false`.

## Uso / tests

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_openapi_f55.py
curl -sS http://127.0.0.1:8765/api/openapi.json | head
```

About → enlace **API (OpenAPI)** abre `/api/openapi.json`. Docs del workbench ya lista `FASE_55_OPENAPI.md`.

## Fuera de alcance

LIVE · FastAPI · Swagger UI embebido · auth WAN · TLS · certificado externo `FASE_55_APPROVED.md` · flip LIVE
