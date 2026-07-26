# Fase 43 — Red-team Workbench Hardening

**Estado:** ✅ **APROBADO_INTERNO** (v0.35.0) — certificado externo `FASE_43_APPROVED.md` **NO** emitido  
**Base:** v0.34.0 · F42 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-087  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F43.md` · noche `INTERNAL_AUDIT_F19_F43_NIGHT.md`

## Objetivo

Auditoría red-team de APIs workbench + remediación fail-closed (path traversal, LIVE, bind host, payloads oversized).

## DoD

- [x] Auditoría `api.py` / `server.py` / session paths
- [x] Tests red-team `tests/unit/workbench/test_redteam_f43.py` (ataques → 400/ValidationError)
- [x] Remediación HIGH/CRITICAL encontrados
- [x] Límite body JSON default **2 MiB** (`DEFAULT_MAX_BODY_BYTES`)
- [x] Docs: `docs/FASE_43_REDTEAM.md` + IMPLEMENTATION_REPORT
- [x] DEC-087 · bump **0.35.0**
- [x] Sin `FASE_43_APPROVED.md` · sin LIVE flip

## Hallazgos remediados

| Sev | Hallazgo | Remediation |
|-----|----------|-------------|
| **HIGH** | `zip_path` aceptaba path arbitrario del FS | Sandbox bajo session parent (`allowed_roots`) |
| **HIGH** | `create_server(host=0.0.0.0)` sin flag | Fail-closed: requiere `allow_non_loopback=True` |
| **HIGH** | `csv_path` con `..` en connect | Reject traversal / null byte |
| **MED** | Body JSON default 1 MiB | Subido a **2 MiB**; import ZIP sigue con techo 55 MiB |
| **MED** | Segmentos URL (`run_id`/`report_id`) solo check `/` | `_path_segment_ok` rechaza `..` y separators |

Controles ya existentes (re-testeados): docs path traversal, LIVE mode reject, session/experiment/report/run id charset, zip-slip F39, launch `--allow-non-loopback`.

## API / contratos tocados

| Superficie | Cambio |
|------------|--------|
| `POST /api/session/import` | `zip_path` solo bajo session parent |
| `create_server(...)` | `allow_non_loopback: bool = False` |
| `_read_json` | `DEFAULT_MAX_BODY_BYTES = 2_000_000` |
| `POST /api/broker/connect` | `csv_path` fail-closed ante `..` |
| URL segments lab | `_path_segment_ok` |

## Tests

`tests/unit/workbench/test_redteam_f43.py` — path traversal, zip sandbox, LIVE, unbound host, oversized body, csv/experiment/docs.

## Fuera de alcance

LIVE flip · auth WAN · Electron · certificado externo `FASE_43_APPROVED.md` · browser E2E · DoS network-layer
