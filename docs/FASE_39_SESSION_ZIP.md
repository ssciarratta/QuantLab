# Fase 39 — Session Export/Import ZIP

**Estado:** ✅ **APROBADO_INTERNO** (v0.31.0) — certificado externo `FASE_39_APPROVED.md` **NO** emitido  
**Base:** v0.30.0 · F38 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-083  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F39.md` · noche `INTERNAL_AUDIT_F19_F39_NIGHT.md`

## Objetivo
Exportar / importar el directorio durable de sesión workbench como ZIP research-safe (sin secretos), con protección zip-slip fail-closed y UI en Settings.

## DoD
- [x] Export session dir → ZIP (journal, book, layout, settings, reports, optimizer, …) sin secretos
- [x] API `GET /api/session/export` → JSON (path/meta) o `?download=1` ZIP
- [x] API `POST /api/session/import` — `mode=new|merge` fail-closed (zip-slip + allowlist + secretos)
- [x] UI Export/Import en panel Settings
- [x] Docs: `docs/FASE_39_SESSION_ZIP.md` + IMPLEMENTATION_REPORT
- [x] Tests zip-slip + roundtrip + QA
- [x] DEC-083 · bump **0.31.0**
- [x] Sin `FASE_39_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/session/export` | JSON: path, filename, sha256, files_count |
| GET | `/api/session/export?download=1` | `application/zip` attachment |
| POST | `/api/session/import` | body: `mode`, `zip_path` **o** `zip_base64`, opcional `session_id` |

Respuesta incluye: `live_blocked`, `live_routing:false`, `research_safe:true`.

### Import modes

| mode | Comportamiento |
|------|----------------|
| `new` | Crea sesión hermana bajo el mismo parent; destino debe estar vacío |
| `merge` | Solo archivos ausentes; **fail-closed** si hay conflicto (no overwrite) |

### Body import

```json
{
  "mode": "new",
  "session_id": "opcional",
  "zip_base64": "...",
  "zip_path": "/abs/path.zip"
}
```

Exactamente uno de `zip_base64` | `zip_path`. Límite ~50 MiB.

## Contenido del ZIP

**Incluye:** `journal.jsonl`, `book.json`, `meta.json`, `layout.json`, `settings.json`, `watchlist.json`, `chat_audit.jsonl`, dirs `experiments/`, `exports/`, `reports/`, `features/`, `validation/`, `optimizer/`, `montecarlo/`, más manifiesto `quantlab_session_export.json`.

**Excluye (secretos):** `.env*`, `*.secret`, `*api_key*`, `*credentials*`, `*password*`, dirs `secrets/` / `credentials/`, etc.

**ZIP escrito en:** `<session_parent>/_session_zips/` (fuera del árbol de sesión).

## UI

- Panel Settings → sección **Export / Import ZIP**
- Exportar sesión · Descargar ZIP · file picker + mode new/merge
- Client: `QLApi.sessionExport` / `sessionImport` / `sessionExportDownloadUrl`

## Notas técnicas
- Módulo: `workbench/session_zip.py`
- Zip-slip: reutiliza `scale.backup._assert_safe_zip_member`
- Escritura: `atomic_io.atomic_write_bytes`
- Merge conflict → `ValidationError` (usar `mode=new` para restore completo)

## Fuera de alcance
LIVE · auth WAN · Electron · certificado externo `FASE_39_APPROVED.md` · browser E2E · overwrite en merge · sync remoto
