# Fase 30 — Universe Watchlist + Data Catalog Browser

**Estado:** ✅ **APROBADO_INTERNO** (v0.22.0) — certificado externo `FASE_30_APPROVED.md` **NO** emitido  
**Base:** v0.21.0 · F29 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-074  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F30.md` · noche `INTERNAL_AUDIT_F19_F30_NIGHT.md`

## Objetivo
Watchlist durable por sesión + panel Universe (broker symbols ∪ watchlist → set symbol Market/Session) y browser read-only del Data Catalog local (`quantlab.data.catalog`).

## DoD
- [x] `watchlist.json` por sesión + add/remove; API `GET`/`PUT` `/api/watchlist`
- [x] Panel Universe: lista broker + watchlist; click → set symbol
- [x] Catalog browser read-only vía `DataCatalog` / SQLite|DuckDB; vacío ok + mensaje
- [x] Panel Catalog UI mínimo
- [x] Docs: `docs/FASE_30_UNIVERSE_CATALOG.md` + IMPLEMENTATION_REPORT
- [x] Tests unitarios F30
- [x] DEC-074 · bump **0.22.0**

## Layout en disco

```text
<data/runtime/workbench>/<session_id>/
  watchlist.json              # { version: 1, symbols: [...] }
```

Catálogo local (fuera de sesión):

```text
data/catalog/quantlab_catalog.sqlite   # default A3
data/catalog/quantlab_catalog.duckdb   # candidato
# o QUANTLAB_CATALOG_PATH=<path>
```

- Símbolos: charset `^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$` (upper), max 256
- Escritura atómica de `watchlist.json`
- Catalog: **no crea** DB si el archivo no existe

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/watchlist` | symbols + watchlist object |
| PUT | `/api/watchlist` | replace (`symbols`) / `add` / `remove` |
| GET | `/api/universe` | broker instruments ∪ watchlist |
| GET | `/api/catalog` | datasets read-only; vacío ok |

## UI

- Menú Sesión → **Universe** · **Data Catalog**
- Universe: add/toggle watchlist; click símbolo → `#md-symbol` / `#ps-symbol` + evento `ql:set-symbol`
- Catalog: tabla dataset_id/kind/provider/symbol/tf; mensaje si ausente

## Notas técnicas
- Reusa `quantlab.data.catalog.DataCatalog` + `SqliteCatalogBackend` / `DuckDBCatalogBackend`
- Sin flip LIVE · sin place_order venue · catalog read-only (sin upsert desde workbench)

## Fuera de alcance
LIVE · auth WAN · escritura/registro datasets · sync remoto catálogo · multi-watchlist
