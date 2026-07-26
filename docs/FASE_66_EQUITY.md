# Fase 66 — Equity Curve Snapshot

**Estado:** ✅ **APROBADO_INTERNO** (v0.58.0) — certificado externo `FASE_66_APPROVED.md` **NO** emitido  
**Base:** v0.57.0 · F65 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-110  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F66.md` · noche `INTERNAL_AUDIT_F19_F66_NIGHT.md`

## Objetivo

Snapshot append-only de equity/cash de la sesión paper (`equity.jsonl`) al aplicar fills y en cada paper session step, con `GET /api/paper/equity` y sparkline en Positions — sin flip LIVE.

## DoD

- [x] Append a `equity.jsonl` (`ts`, `equity`, `cash`) al aplicar fills (`on_book_change`)
- [x] Append en cada paper session step (`on_step`)
- [x] `GET /api/paper/equity?limit=N` → últimos N puntos
- [x] Sección Equity en Positions: lista + sparkline SVG
- [x] OpenAPI catalog route
- [x] Docs: `docs/FASE_66_EQUITY.md` + IMPLEMENTATION_REPORT
- [x] Tests `test_equity_curve_f66.py` + smoke F66
- [x] DEC-110 · bump **0.58.0**
- [x] Sin `FASE_66_APPROVED.md` · sin LIVE

## API

| Método | Path | Notas |
|--------|------|-------|
| GET | `/api/paper/equity` | JSON `{points:[{ts,equity,cash},…]}` últimos N (default 200, max 2000) |

## UI

| Panel | Acción |
|-------|--------|
| Positions | Sección **Equity curve** — sparkline SVG + tabla últimos puntos |

## Notas técnicas

- Path sesión: `<session>/equity.jsonl` (incluido en session ZIP F39)
- Valores `equity`/`cash` como string Decimal-safe
- Best-effort: fallos de append no tumban submit/step
- No toca venue submit / LIVE

## Fuera de alcance

LIVE · auth WAN · charting avanzado · PnL attribution · certificado externo `FASE_66_APPROVED.md` · browser E2E
