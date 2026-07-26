# Fase 23 — Paper Book + Session durable + Risk paper

**Estado:** IMPLEMENTADO (v0.15.0)  
**Base:** v0.14.0 · F19–F22 APROBADO_INTERNO  
**LIVE:** BLOQUEADO (sin flip)

## Objetivo
Libro paper realista: fills → posiciones/cash/equity; sesión durable; risk fail-closed en paper submit.

## DoD
- [x] `PaperBook` (posiciones, cash, avg, MTM)
- [x] `PaperBroker` actualiza book; `get_positions`/`get_account` desde book
- [x] Session root `data/runtime/workbench/<id>/` recuperable
- [x] `GET /api/broker/positions`, `GET /api/paper/book`
- [x] Risk paper (max qty/notional/symbols) en submit
- [x] Panel Positions en UI
- [x] Tests verdes; `LIVE_BLOCKED is True`

## Fuera de alcance
LIVE orders · MD real A3 (F24) · launcher .desktop (F25)
