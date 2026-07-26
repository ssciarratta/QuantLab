# Fase 56 — Security Headers

**Estado:** ✅ **APROBADO_INTERNO** (v0.48.0) — certificado externo `FASE_56_APPROVED.md` **NO** emitido  
**Base:** v0.47.0 · F55 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-100  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F56.md` · noche `INTERNAL_AUDIT_F19_F56_NIGHT.md`

## Objetivo

Endurecer respuestas HTTP del workbench con headers de seguridad baseline y CORS fail-closed (loopback-first):

- **nosniff / DENY / no-referrer** en respuestas workbench.
- **`Cache-Control: no-store`** en `/api/*`.
- **CORS:** nunca `Access-Control-Allow-Origin: *`; Origin presente y no-loopback → no reflejar.

## DoD

- [x] Headers en respuestas: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`
- [x] `Cache-Control: no-store` en `/api/*`
- [x] CORS fail-closed (no `*`; no reflejar Origin non-loopback)
- [x] Módulo `quantlab.workbench.security_headers`
- [x] Suite `tests/unit/workbench/test_security_headers_f56.py`
- [x] Spec + IMPLEMENTATION_REPORT
- [x] Smoke F56 + bundle default F19–F56
- [x] DEC-100 · bump **0.48.0**
- [x] Sin `FASE_56_APPROVED.md` · sin LIVE

## Diseño

| Artefacto | Rol |
|-----------|-----|
| `security_headers.SECURITY_HEADERS` | nosniff / DENY / no-referrer |
| `cors_allow_origin(origin)` | ACAO solo si Origin loopback; nunca `*` |
| `server._apply_security_headers` | Aplica en `_send` / download / 429 |

### CORS (fail-closed)

1. Nunca emitir `Access-Control-Allow-Origin: *`.
2. Si `Origin` ausente / inválido / `null` / `*` → no header ACAO.
3. Si `Origin` host **no** es loopback (`127.0.0.1` / `::1` / `localhost`) → **no reflejar**.
4. Si `Origin` es loopback → se puede reflejar el valor exacto (misma máquina).

## Uso / tests

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_security_headers_f56.py
curl -sSI http://127.0.0.1:8765/api/health | grep -Ei 'x-content-type|x-frame|referrer|cache-control|access-control'
```

## Fuera de alcance

LIVE · auth WAN · TLS · HSTS · certificado externo `FASE_56_APPROVED.md` · flip LIVE

> CSP completa → **Fase 57** (`docs/FASE_57_CSP.md`).
