# Fase 54 — Readiness / Liveness Probes

**Estado:** ✅ **APROBADO_INTERNO** (v0.46.0) — certificado externo `FASE_54_APPROVED.md` **NO** emitido  
**Base:** v0.45.0 · F53 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-098  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F54.md` · noche `INTERNAL_AUDIT_F19_F54_NIGHT.md`

## Objetivo

Exponer probes HTTP estándar para Docker HEALTHCHECK / orquestadores:

- **Liveness** — el proceso HTTP está vivo.
- **Readiness** — el workbench está listo para tráfico research-safe (LIVE bloqueado + session root escribible).

## DoD

- [x] `GET /api/livez` — siempre **200** si el proceso responde
- [x] `GET /api/readyz` — **200** si `LIVE_BLOCKED is True` **y** session root writable; **503** si no
- [x] Módulo `quantlab.workbench.probes`
- [x] Ops: `docs/ops/DOCKER_WORKBENCH.md` documenta HEALTHCHECK con probes
- [x] Spec + IMPLEMENTATION_REPORT
- [x] Suite `tests/unit/workbench/test_probes_f54.py`
- [x] Smoke F54 + bundle default F19–F54
- [x] DEC-098 · bump **0.46.0**
- [x] Sin `FASE_54_APPROVED.md` · sin LIVE

## Diseño

| Endpoint | Status | Condición |
|----------|--------|-----------|
| `GET /api/livez` | 200 | Handler alcanzable (proceso up) |
| `GET /api/readyz` | 200 | `LIVE_BLOCKED is True` + session root writable |
| `GET /api/readyz` | 503 | Gate LIVE no True **o** root no writable |

### Checks de readiness

1. `live_blocked` — `LIVE_BLOCKED is True` (invariante workbench).
2. `session_root_writable` — create+unlink de `.readyz_write_probe` bajo el session root.

`/api/health` sigue siendo el health report rico (F20+); los probes son delgados para orchestrators.

## Uso / tests

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_probes_f54.py
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/api/livez   # 200
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/api/readyz  # 200|503
```

Docker HEALTHCHECK (ejemplo en ops):

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/livez')"
```

## Fuera de alcance

LIVE · auth WAN · TLS · Kubernetes manifests · certificado externo `FASE_54_APPROVED.md` · flip LIVE
