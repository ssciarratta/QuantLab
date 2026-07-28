# Fase 38 — Docs / Help Browser

**Estado:** ✅ **APROBADO_INTERNO** (v0.30.0) — certificado externo `FASE_38_APPROVED.md` **NO** emitido  
**Base:** v0.29.0 · F37 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-082  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F38.md` · noche `INTERNAL_AUDIT_F19_F38_NIGHT.md`

## Objetivo
Panel Help/Docs read-only: listar y previsualizar markdown local bajo `docs/*.md` y `docs/ops/*.md`, con path traversal fail-closed. Integrar con chat `search_docs`.

## DoD
- [x] API `GET /api/docs` — lista `docs/*.md` y `docs/ops/*.md` (paths relativos safe)
- [x] API `GET /api/docs/content?path=` — lee markdown solo bajo `docs/` (traversal fail-closed)
- [x] Panel Help/Docs: buscar + preview markdown→HTML simple (escape) o pre text
- [x] Chat `search_docs` incluye `docs/ops/*.md` (mismo browser)
- [x] Docs: `docs/FASE_38_DOCS_HELP.md` + IMPLEMENTATION_REPORT
- [x] Tests path traversal + list + QA
- [x] DEC-082 · bump **0.30.0**
- [x] Sin `FASE_38_APPROVED.md`

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/docs` | lista docs root + ops; `docs[].path` relativo |
| GET | `/api/docs/content?path=` | contenido + `html` simple escapado |

Respuesta incluye: `live_blocked`, `live_routing:false`, `research_safe:true`.

**No** incluye flip LIVE / place_order / lectura fuera de `docs/` o `docs/ops/`.

## Paths permitidos

| Relativo | Ejemplo |
|----------|---------|
| `*.md` en raíz docs | `GUIA_COMPLETA_QUANTLAB.md` |
| `ops/*.md` | `ops/WORKBENCH_1CLICK.md` |
| `manuales/*.md` | `manuales/00-INDICE.md` (extensión tip 2026-07-27) |
| `montecarlo/*.md` | `montecarlo/montecarlo-guide.md` |
| `scanner/*.md` | `scanner/alpha-scanner-guide.md` |

Rechazados (fail-closed): `..`, absolutos, `audit/…`, otros subdirs, no-`.md`, symlinks fuera de raíz.

### Extensión tip (post-F38)

Allowlist ampliada a `manuales`, `montecarlo`, `scanner` para que Help / Docs muestre los instructivos de usuario sin servir `docs/audit/`. Tests: `tests/unit/workbench/test_docs_f38.py`.


## UI

- Panel `#docs` / start menu **Help / Docs** / command palette `open.docs`
- Buscar por título/path; lista + preview HTML|Texto
- Script: `static/js/panes/docs.js` → `QLPanes.createDocsPane`
- Client: `QLApi.docsList` / `docsContent`

## Notas técnicas
- Persistencia N/A (read-only filesystem repo)
- Módulo: `workbench/docs_browser.py`
- Chat reutiliza `search_docs_files`

## Fuera de alcance
LIVE · auth WAN · Electron · certificado externo `FASE_38_APPROVED.md` · browser E2E · editar docs · servir `docs/audit/`
