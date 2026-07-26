# FASE 69 — Implementation Report (Risk Utilization Report)

**Fecha:** 2026-07-26  
**Versión:** 0.61.0  
**Branch:** `cursor/modo-real-workbench-aafd`  
**Prereq:** F68 Milestone Freeze · F25 Risk panel · F23 PaperRiskLimits  
**Impl SHA:** *(tip post-commit)*  
**Alcance:** `GET /api/risk/utilization` + sección Utilización en Risk — **sin flip LIVE**

---

## Entregas

| ID | Entrega | Path |
|----|---------|------|
| D1 | compute_risk_utilization helpers | `workbench/risk_utilization.py` |
| D2 | API handler + HTTP route | `api.py` · `server.py` · `api_catalog.py` |
| D3 | UI Risk utilization section | `risk.js` · `api.js` |
| D4 | Spec + DEC-113 + bump | `docs/FASE_69_RISK_UTIL.md` · **0.61.0** |
| D5 | Tests HTTP + UI | `tests/unit/workbench/test_risk_utilization_f69.py` |
| D6 | Smoke F69 | `scripts/internal_audit_smoke.py` |
| D7 | Implementation report | este doc |

## Invariantes

- `LIVE_BLOCKED is True`
- Sin `FASE_69_APPROVED.md`
- Sin flip LIVE / place_order venue
- DEC-113
- `phases_summary == "F19–F69 INTERNAL"`
- About `version` ≡ `__version__` · **0.61.0**

## QA

```text
export PATH="$HOME/.local/bin:$PATH"
uv sync --extra dev
uv run ruff check src/quantlab tests scripts
uv run mypy --strict src/quantlab
uv run pytest -q
uv run quantlab-health
uv run python scripts/internal_audit_smoke.py
```

## Fuera de alcance (correcto)

- Flip `LIVE_BLOCKED`
- Auth WAN / Electron
- Certificado externo `FASE_69_APPROVED.md`
- Hard-block portfolio por % utilización
