# Fase 44 — E2E Paper Workflow Integration Test

**Estado:** ✅ **APROBADO_INTERNO** (v0.36.0) — certificado externo `FASE_44_APPROVED.md` **NO** emitido  
**Base:** v0.35.0 · F43 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (`LIVE_BLOCKED=True`)  
**DEC:** DEC-088  
**INTERNAL:** `docs/audit/INTERNAL_AUDIT_F44.md` · noche `INTERNAL_AUDIT_F19_F44_NIGHT.md`

## Objetivo

Test de integración (sin browser) que ejercita el flujo paper completo vía API workbench en un servidor loopback en thread.

## DoD

- [x] Boot server loopback (`workbench_server` fixture)
- [x] Set mode paper
- [x] Connect venue binance + a3 (tester) → PaperBroker
- [x] Submit paper order
- [x] Check positions / book
- [x] Start paper session `buy_once` + step
- [x] Run backtest + list reports
- [x] Run validation + optimize + mc (mini)
- [x] Export HB
- [x] Export session zip (JSON path + download bytes)
- [x] Assert LIVE still blocked / mode live rejected
- [x] Docs: `docs/FASE_44_E2E_WORKFLOW.md` + IMPLEMENTATION_REPORT
- [x] DEC-088 · bump **0.36.0**
- [x] Sin `FASE_44_APPROVED.md` · sin LIVE flip · sin browser E2E

## Flujo ejercitado

| # | Paso | Endpoint |
|---|------|----------|
| 1 | Health | `GET /api/health` |
| 2 | Mode paper | `POST /api/mode` |
| 3 | Connect binance/a3 tester | `POST /api/broker/connect` |
| 4 | Paper submit | `POST /api/paper/submit` |
| 5 | Positions + book | `GET /api/broker/positions` · `GET /api/paper/book` |
| 6 | Session buy_once + step | `POST /api/paper/session/{start,step,stop}` |
| 7 | Backtest + reports | `POST /api/lab/backtest` · `GET /api/lab/reports` |
| 8 | Validation / optimize / MC | `POST /api/lab/validation/run` · optimize · montecarlo |
| 9 | Export HB | `POST /api/lab/export-hb` |
| 10 | Session ZIP | `GET /api/session/export` (+ `?download=1`) |
| 11 | LIVE reject | `POST /api/mode` `live` → 400 |

## Tests

`tests/unit/workbench/test_e2e_paper_workflow_f44.py`

## Fuera de alcance

LIVE flip · auth WAN · Electron · certificado externo `FASE_44_APPROVED.md` · browser E2E · Playwright
