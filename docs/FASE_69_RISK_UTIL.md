# Fase 69 — Risk Utilization Report

**Estado:** ✅ **APROBADO_INTERNO** (v0.61.0) — certificado externo `FASE_69_APPROVED.md` **NO** emitido  
**Base:** v0.60.0 · F68 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-113  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F69.md` · noche `INTERNAL_AUDIT_F19_F69_NIGHT.md`

## Objetivo

Reportar el **% de utilización** de `max_qty` / `max_notional` frente al book/posiciones paper, expuesto vía `GET /api/risk/utilization` y visible en el panel Riesgo — sin flip LIVE.

## DoD

- [x] `compute_risk_utilization(book, limits, marks)` — peak qty + gross notional Decimal-safe
- [x] `GET /api/risk/utilization` — marks broker (mid/last) o avg fallback
- [x] Sección Utilización en panel Risk
- [x] OpenAPI catalog route
- [x] Docs: `docs/FASE_69_RISK_UTIL.md` + IMPLEMENTATION_REPORT
- [x] Tests `test_risk_utilization_f69.py` + smoke F69
- [x] DEC-113 · bump **0.61.0**
- [x] Sin `FASE_69_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/risk/utilization` | JSON `{used,pct,positions,limits,…}` Decimal-safe strings |

### Convención

- `used.qty` = max \|qty\| entre posiciones abiertas (pico vs `max_qty`)
- `used.notional` = Σ \|qty × mark\| (exposición bruta vs `max_notional`)
- `pct.qty` / `pct.notional` = used / limit × 100 (puede superar 100)
- Por posición: `qty`, `mark`, `notional`, `pct_qty`, `pct_notional`
- Marks: PaperBroker mid/last o avg_price fallback

## UI

| Panel | Acción |
|-------|--------|
| Risk | Sección **Utilización** — kv used/pct + breakdown por símbolo |

## Fuera de alcance

LIVE · auth WAN · hard-block por % portfolio · certificado externo `FASE_69_APPROVED.md` · browser E2E
