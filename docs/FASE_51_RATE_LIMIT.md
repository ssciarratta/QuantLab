# Fase 51 — API Rate Limit (loopback soft)

**Estado:** ✅ **APROBADO_INTERNO** (v0.43.0) — certificado externo `FASE_51_APPROVED.md` **NO** emitido  
**Base:** v0.42.0 · F50 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-095  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F51.md` · noche `INTERNAL_AUDIT_F19_F51_NIGHT.md`

## Objetivo

Soft rate limit in-process del Workbench HTTP API (loopback), keyed por **IP + path**, con default alto para no romper tests/perf, y 429 JSON al exceder.

## DoD

- [x] Módulo `quantlab.workbench.rate_limit` (token bucket thread-safe)
- [x] Integración en `server.py` (GET/POST/PUT) antes del routing
- [x] Default **120 req/s** · burst 120 (configurable / inyectable)
- [x] 429 JSON `{ok:false, code:rate_limit_exceeded, ...}` + `Retry-After`
- [x] Suite `tests/unit/workbench/test_rate_limit_f51.py` (límite bajo inyectado)
- [x] Docs: `docs/FASE_51_RATE_LIMIT.md` + IMPLEMENTATION_REPORT
- [x] Smoke F51 + bundle default F19–F51
- [x] DEC-095 · bump **0.43.0**
- [x] Sin `FASE_51_APPROVED.md` · sin LIVE

## Diseño

| Campo | Valor |
|-------|-------|
| Algoritmo | Token bucket (refill continuo) |
| Clave | `client_ip \| path` (path sin query) |
| Default RPS | `120` |
| Default burst | `120` |
| Scope | In-process (por proceso / `WorkbenchState.rate_limiter`) |
| Inyección | `WorkbenchState.configure_rate_limit(RateLimitConfig(...))` |

Respuesta al exceder:

```json
{
  "ok": false,
  "error": "rate limit exceeded (2 req/s per IP/path); retry after 0.500s",
  "code": "rate_limit_exceeded",
  "limit_rps": 2.0,
  "retry_after_s": 0.5
}
```

Header HTTP: `Retry-After: <seconds entero ceil>`.

## Uso / tests

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_rate_limit_f51.py
# Inyectar límite bajo en servidor efímero:
# state.configure_rate_limit(RateLimitConfig(requests_per_second=2, burst=2))
```

## Fuera de alcance

LIVE · auth WAN · Redis / rate limit distribuido · Electron · browser E2E · certificado externo `FASE_51_APPROVED.md`
