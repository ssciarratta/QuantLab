# Fase 67 — Paper PnL Summary

**Estado:** ✅ **APROBADO_INTERNO** (v0.59.0) — certificado externo `FASE_67_APPROVED.md` **NO** emitido  
**Base:** v0.58.0 · F66 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-111  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F67.md` · noche `INTERNAL_AUDIT_F19_F67_NIGHT.md`

## Objetivo

Resumen de PnL paper (realized / unrealized / equity / cash) desde `PaperBook` + marks MTM, expuesto vía `GET /api/paper/pnl` y visible en headers de Positions / Blotter — sin flip LIVE.

## DoD

- [x] `PaperBook.get_pnl(marks)` — realized/unrealized/equity/cash Decimal-safe
- [x] `GET /api/paper/pnl` — marks broker (mid/last) o avg fallback
- [x] Header PnL en Positions y Blotter
- [x] OpenAPI catalog route
- [x] Docs: `docs/FASE_67_PNL.md` + IMPLEMENTATION_REPORT
- [x] Tests `test_paper_pnl_f67.py` + smoke F67
- [x] DEC-111 · bump **0.59.0**
- [x] Sin `FASE_67_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/paper/pnl` | JSON `{realized,unrealized,equity,cash,…}` Decimal-safe strings |

### Convención

- `cost` = Σ(qty × avg_price) posiciones abiertas
- `mtm` = Σ(qty × mark) (fallback avg)
- `unrealized` = mtm − cost
- `realized` = cash + cost − initial_cash
- `equity` = cash + mtm = initial_cash + realized + unrealized
- PnL bruto sin fees (TD-17)

## UI

| Panel | Acción |
|-------|--------|
| Positions | Header + kv realized/unrealized/equity/cash |
| Blotter | Header `Cuenta / PnL` con mismas cifras |

## Fuera de alcance

LIVE · auth WAN · attribution por símbolo · fees en PnL · certificado externo `FASE_67_APPROVED.md` · browser E2E
