# FASE 43 — Implementation Report (Red-team Workbench Hardening)

**Fecha:** 2026-07-26  
**Versión:** 0.35.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F42 Ops Metrics Panel  
**Impl SHA:** `2b90b1f`  
**Alcance:** auditoría red-team + remediación fail-closed — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| A1 | Body 2 MiB + path segment gate | `workbench/server.py` |
| A2 | `create_server` loopback fail-closed | `server.py` · `launch.py` |
| A3 | `zip_path` sandbox `allowed_roots` | `session_zip.py` · `api.py` |
| A4 | `csv_path` traversal reject | `api.py` |
| T1 | Tests red-team F43 | `tests/unit/workbench/test_redteam_f43.py` |
| T2 | Smoke F43 | `scripts/internal_audit_smoke.py` |
| D1 | Spec + DEC-087 + bump | `docs/FASE_43_REDTEAM.md` · `0.35.0` |
| D2 | Implementation report | este doc |

## Remediaciones

1. **HIGH** — `zip_path` arbitrario → sandbox session parent.  
2. **HIGH** — bind `0.0.0.0` vía `create_server` sin flag → `ValidationError`.  
3. **HIGH** — `csv_path` con `..` → `ApiError(400)`.  
4. **MED** — body default 2 MiB; segmentos URL anti-`..`.

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_43_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-087

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff format src/quantlab tests/unit/workbench
uv run ruff check src/quantlab tests/unit/workbench
uv run mypy --strict src/quantlab
uv run pytest tests/unit/workbench/test_redteam_f43.py -q
uv run pytest tests/unit/workbench -q
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Browser E2E
- Certificado externo `FASE_43_APPROVED.md`
