# INTERNAL AUDIT — F57 Content-Security-Policy

**Fecha:** 2026-07-26  
**Auditor:** Meta-Auditor INTERNO Zero-Trust  
**Veredicto:** **APROBADO_INTERNO**  
**Código tip:** `fbb0355` · **v0.49.0** · F57 Content-Security-Policy  
**Certificado externo:** **NO emitido** (`FASE_57_APPROVED.md` ausente a propósito)

---

## Checklist

| Campo | Valor |
|-------|-------|
| Versión | **0.49.0** |
| LIVE_BLOCKED | **True** |
| DEC | DEC-101 |
| Suite | `test_csp_f57.py` |
| Smoke | F57 en `internal_audit_smoke.py` |
| Bundle | F19–F57 |

## Evidencia revisada

1. Header `Content-Security-Policy` en respuestas workbench (API + static).  
2. Política: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'`.  
3. Sin `unsafe-eval`; `index.html` sin scripts inline (solo `/static/js/*`).  
4. Extensión `CONTENT_SECURITY_POLICY` en `quantlab.workbench.security_headers` (F56 headers intactos).  
5. Suite F57 (unit + HTTP).  
6. DEC-101 · bump 0.49.0 · `phases_summary` F19–F57 INTERNAL.  
7. QA: mypy strict 181 · ruff · pytest **906** · quantlab-health **0.49.0** · smoke **43/43 PASS**.  

## Veredicto

CSP restrictiva SPA local · bump 0.49.0 · sin flip LIVE · sin `FASE_57_APPROVED`.

---

Meta-Auditor INTERNO Zero-Trust · 2026-07-26 · QuantLab F57 · **APROBADO_INTERNO** · **sin** certificado externo · **LIVE_BLOCKED** intacto
