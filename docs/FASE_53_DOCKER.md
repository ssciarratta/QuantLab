# Fase 53 — Dockerfile Workbench (opt-in)

**Estado:** ✅ **APROBADO_INTERNO** (v0.45.0) — certificado externo `FASE_53_APPROVED.md` **NO** emitido  
**Base:** v0.44.0 · F52 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-097  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F53.md` · noche `INTERNAL_AUDIT_F19_F53_NIGHT.md`

## Objetivo

Entregar una imagen Docker **opt-in** del Workbench para Docker Desktop / lab local, con bind documentado `0.0.0.0` + `--allow-non-loopback` **solo** para port-map, publicando el puerto en loopback del host (`127.0.0.1:8765`).

## DoD

- [x] `Dockerfile.workbench` — `python:3.12-slim`, `uv sync`, `EXPOSE 8765`, CMD con `--allow-non-loopback` / `--no-browser`
- [x] `.dockerignore` (sin `.env`, data secrets, venvs, reports pesados)
- [x] Ops: `docs/ops/DOCKER_WORKBENCH.md` (`-p 127.0.0.1:8765:8765`)
- [x] Spec + IMPLEMENTATION_REPORT
- [x] Suite parse Dockerfile (sin build obligatorio si Docker ausente)
- [x] Smoke F53 + bundle default F19–F53
- [x] DEC-097 · bump **0.45.0**
- [x] Sin `FASE_53_APPROVED.md` · sin LIVE

## Diseño

| Campo | Valor |
|-------|-------|
| Base image | `python:3.12-slim-bookworm` |
| Package manager | `uv` (binary from `ghcr.io/astral-sh/uv`) |
| Sync | `uv sync --frozen --no-dev` |
| Port | `EXPOSE 8765` |
| CMD | `quantlab-workbench --host 0.0.0.0 --allow-non-loopback --no-browser` |
| Publish seguro | `-p 127.0.0.1:8765:8765` |
| Auth HTTP | ninguna (igual que F20/F25) |

### Riesgo documentado

`--allow-non-loopback` + bind `0.0.0.0` es **intencional** para Docker Desktop port mapping. Sin auth. Nunca publicar a WAN / `0.0.0.0` en el host.

## Uso / tests

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run pytest -q tests/unit/workbench/test_dockerfile_f53.py
# Opcional (si Docker disponible):
# docker build -f Dockerfile.workbench -t quantlab-workbench .
# docker run --rm -p 127.0.0.1:8765:8765 quantlab-workbench
```

## Fuera de alcance

LIVE · auth WAN · TLS · Kubernetes · certificado externo `FASE_53_APPROVED.md` · build obligatorio en CI
