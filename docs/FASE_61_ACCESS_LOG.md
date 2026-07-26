# Fase 61 — Workbench Request Access Log

**Estado:** ✅ **APROBADO_INTERNO** (v0.53.0) — certificado externo `FASE_61_APPROVED.md` **NO** emitido  
**Base:** v0.52.0 · F60 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-105  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F61.md` · noche `INTERNAL_AUDIT_F19_F61_NIGHT.md`

## Objetivo

Log append-only de requests HTTP del workbench por sesión (`access.jsonl`) con metadata mínima (method, path, status, ms), toggle en settings y API de lectura — sin bodies/secrets y sin flip LIVE.

## DoD

- [x] `access.jsonl` append-only en sesión (method, path, status, ms)
- [x] Settings `access_log: true` (default true) · toggle UI
- [x] API `GET /api/access-log?limit=100`
- [x] Middleware server registra en `_send` / rate-limit 429
- [x] Suite `tests/unit/workbench/test_access_log_f61.py`
- [x] Spec + IMPLEMENTATION_REPORT
- [x] Smoke F61 + bundle default F19–F61
- [x] DEC-105 · bump **0.53.0**
- [x] Sin `FASE_61_APPROVED.md` · sin LIVE

## Diseño

| Artefacto | Rol |
|-----------|-----|
| `workbench/access_log.py` | `AccessLog` append-only + `list_access_log` |
| `session/access.jsonl` | Persistencia por sesión (ZIP export F39) |
| `settings.access_log` | Bool default `true` |
| `server.py` | `_begin_access` / `_finish_access` (ms) |
| `GET /api/access-log` | Tail JSON (default 100, max 500) |

### Línea JSONL

```json
{"ts":"…","method":"GET","path":"/api/health","status":200,"ms":0.42,"live_blocked":true}
```

Sin `body`, sin `headers`, sin query string (path sanitizado).

### API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/access-log?limit=100` | Últimos N eventos |

Respuesta: `ok`, `kind:access_log`, `count`, `events`, `fields`, `access_log_enabled`, `session_id`, `live_blocked`, `live_routing:false`, `research_safe:true`.

### Uso

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_access_log_f61.py
# GET /api/access-log?limit=100
```

## Fuera de alcance

LIVE · auth WAN · log de bodies/headers · certificado externo `FASE_61_APPROVED.md` · flip LIVE · rewrite/truncate del log
