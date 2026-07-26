# Fase 52 — Graceful Shutdown + Paper Session Safety

**Estado:** ✅ **APROBADO_INTERNO** (v0.44.0) — certificado externo `FASE_52_APPROVED.md` **NO** emitido  
**Base:** v0.43.0 · F51 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-096  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F52.md` · noche `INTERNAL_AUDIT_F19_F52_NIGHT.md`

## Objetivo

Apagado ordenado del Workbench: al recibir SIGINT/SIGTERM (o `POST /api/shutdown` loopback), detener el paper session runner si corre, flushear layout/settings (+ book) y apagar el HTTPServer sin dejar runners huérfanos.

## DoD

- [x] Módulo `quantlab.workbench.shutdown` (stop paper + flush + flag + server.shutdown)
- [x] Handlers SIGINT/SIGTERM en `launch.py` → `perform_graceful_shutdown`
- [x] `POST /api/shutdown` **solo loopback** (403 si peer no-loopback)
- [x] Flag `shutdown_requested` / `shutdown_done` en `WorkbenchState`
- [x] Suite `tests/unit/workbench/test_shutdown_f52.py` (stop session on shutdown hook)
- [x] Docs: `docs/FASE_52_SHUTDOWN.md` + IMPLEMENTATION_REPORT
- [x] Smoke F52 + bundle default F19–F52
- [x] DEC-096 · bump **0.44.0**
- [x] Sin `FASE_52_APPROVED.md` · sin LIVE

## Diseño

| Campo | Valor |
|-------|-------|
| Señales | SIGINT · SIGTERM → graceful shutdown |
| API | `POST /api/shutdown` loopback-only |
| Orden | paper stop → flush layout/settings/book → flag → `server.shutdown()` (otro hilo) |
| Idempotencia | `shutdown_done` evita doble stop/shutdown |
| Uso API | Tests / automatización; usuario normal = Ctrl+C / SIGTERM |

Respuesta API (loopback):

```json
{
  "ok": true,
  "kind": "shutdown",
  "reason": "api:/api/shutdown",
  "paper": {"stopped": true, "was_running": true, "status": {"running": false}},
  "flushed": {"layout": true, "settings": true, "book": true},
  "shutdown_requested": true,
  "live_blocked": true
}
```

Peer no-loopback → **403** JSON.

## Uso / tests

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_shutdown_f52.py
# En proceso: Ctrl+C / kill -TERM <pid>
# Automatización (solo loopback):
#   curl -X POST http://127.0.0.1:8765/api/shutdown -H 'Content-Type: application/json' -d '{}'
```

## Fuera de alcance

LIVE · auth WAN · Electron · browser E2E · certificado externo `FASE_52_APPROVED.md`
