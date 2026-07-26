# Fase 57 — Content-Security-Policy

**Estado:** ✅ **APROBADO_INTERNO** (v0.49.0) — certificado externo `FASE_57_APPROVED.md` **NO** emitido  
**Base:** v0.48.0 · F56 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-101  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F57.md` · noche `INTERNAL_AUDIT_F19_F57_NIGHT.md`

## Objetivo

Emitir `Content-Security-Policy` restrictiva compatible con la SPA local del workbench:

- **`default-src 'self'`**
- **`script-src 'self'`** (sin inline scripts; sin `unsafe-eval`)
- **`style-src 'self' 'unsafe-inline'`** (atributos `style=` en panes JS existentes)
- **`connect-src 'self'`** (fetch API solo al mismo origen)
- **`frame-ancestors 'none'`** (complementa `X-Frame-Options: DENY`)

## DoD

- [x] Header CSP en respuestas workbench (API + static)
- [x] Política sin `unsafe-eval`
- [x] `index.html` sin `<script>` inline — solo `/static/js/*`
- [x] Extensión de `quantlab.workbench.security_headers` (`CONTENT_SECURITY_POLICY`)
- [x] Suite `tests/unit/workbench/test_csp_f57.py`
- [x] Spec + IMPLEMENTATION_REPORT
- [x] Smoke F57 + bundle default F19–F57
- [x] DEC-101 · bump **0.49.0**
- [x] Sin `FASE_57_APPROVED.md` · sin LIVE

## Diseño

| Artefacto | Rol |
|-----------|-----|
| `CONTENT_SECURITY_POLICY` | String canónico CSP |
| `SECURITY_HEADERS["Content-Security-Policy"]` | Incluido en toda respuesta vía `_apply_security_headers` |
| `index.html` | Solo `<script src="/static/js/...">` externos |

### Política canónica

```text
default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'
```

### Notas SPA

- Los panes generan HTML con `style="..."` → hace falta `'unsafe-inline'` en `style-src`.
- Journal export CSV usa `Blob` + `URL.createObjectURL` + `<a download>` (no carga el blob como documento navegable).
- No CDN / no fonts externas / no workers.

## Uso / tests

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_csp_f57.py
curl -sSI http://127.0.0.1:8765/ | grep -i content-security-policy
```

## Fuera de alcance

LIVE · auth WAN · TLS · HSTS · nonce/hash estricto en style · certificado externo `FASE_57_APPROVED.md` · flip LIVE
