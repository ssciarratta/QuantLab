# Fase 23 — Paper Book + Session durable + Risk paper

**Estado:** APROBADO_INTERNO (v0.15.0) — certificado externo pendiente  
**Base:** v0.14.0 · F19–F22 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (sin flip)  
**Audit INTERNAL:** `docs/audit/INTERNAL_AUDIT_F23.md` · `AUTO_AUDIT_2026-07-26_F23.md`  
**Review Package INTERNAL:** `docs/audit/FASE_23_REVIEW_PACKAGE.md`  
**Impl:** `9b89274`

## Objetivo
Libro paper realista: fills → posiciones/cash/equity; sesión durable; risk fail-closed en paper submit.

## DoD
- [x] `PaperBook` (posiciones, cash, avg, MTM)
- [x] `PaperBroker` actualiza book; `get_positions`/`get_account` desde book
- [x] Session root `data/runtime/workbench/<id>/` recuperable
- [x] `session_id` path-safe (`validate_session_id`; anti-traversal)
- [x] `GET /api/broker/positions`, `GET /api/paper/book`
- [x] Risk paper (max qty/notional/symbols) en submit
- [x] Panel Positions en UI
- [x] Tests verdes; `LIVE_BLOCKED is True`
- [x] Audit INTERNAL Zero-Trust = **APROBADO_INTERNO** (sin `FASE_23_APPROVED.md`)

## Fuera de alcance
LIVE orders · MD real A3 (F24) · launcher .desktop (F25)
