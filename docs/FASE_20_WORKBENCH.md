# Fase 20 — Workbench (1-click, ventanas tipo Windows)

**Estado:** IMPLEMENTADO (v0.12.0) · **APROBADO_INTERNO** Zero-Trust (2026-07-26)  
**Prerrequisito:** F19 Operating Modes + BrokerPort  
**Pedido dueño:** entrar con 1 click; ventanas tipo Windows; mouse; todas las funcionalidades.  
**Certificado externo:** NO emitido (`FASE_20_APPROVED.md` reserva Meta-Auditor externo).  
**Evidencia INTERNAL:** `docs/audit/INTERNAL_AUDIT_F20.md` · `AUTO_AUDIT_2026-07-26_F20.md` · `FASE_20_REVIEW_PACKAGE.md`

## Stack (DEC-061)

`stdlib http.server` + SPA estática con window-manager (sin deps UI nuevas).

```text
src/quantlab/workbench/
├── launch.py          # CLI: --host --port --no-browser --mode
├── server.py          # ThreadingHTTPServer
├── api.py             # JSON API + WorkbenchState
└── static/            # index.html, css, js/wm.js, panes
```

Bind default: `127.0.0.1`. Entry: `quantlab-workbench`.

## Paneles F20 (shell)

1. Health / Mode  
2. Market Data  
3. Paper Blotter  

## API (loopback)

| Método | Ruta | Notas |
|--------|------|-------|
| GET | `/api/health` | `run_health_checks().to_dict()` |
| GET/POST | `/api/mode` | LIVE → 400; `real` → paper |
| GET | `/api/venues` | registry |
| POST | `/api/broker/connect` | siempre envuelve PaperBroker |
| GET | `/api/broker/instruments\|snapshot\|account` | MD vía PaperBroker |
| POST | `/api/paper/submit` | solo TESTER/PAPER |
| GET | `/api/paper/fills` | journal sesión |
| GET | `/` + `/static/…` + `/api/static/…` | SPA |

## Seguridad

- Bind `127.0.0.1` por defecto  
- Rechazo de `OperatingMode.LIVE` y de cualquier path que envíe `place_order` al venue  
- Banner UI: mode + `LIVE_BLOCKED`  
- `LIVE_BLOCKED` permanece `True` (sin flip)

## Definition of Done

- [x] Paquete `src/quantlab/workbench/` con launch/server/api + static SPA
- [x] Entry `quantlab-workbench` en pyproject (v0.12.0)
- [x] Bind default loopback; API JSON completa F20
- [x] Window-manager MDI (drag/resize/minimize/close + taskbar)
- [x] 3 ventanas: Health, Market Data, Paper Blotter (UI ES)
- [x] Paper submit solo PaperBroker; LIVE rechazado
- [x] Tests `tests/unit/workbench/` (http.client + thread + puerto efímero)
- [x] QA: ruff / mypy --strict / pytest workbench+brokers / quantlab-health
- [x] Docs DoD + implementation report
- [x] Autauditoría + Review Package INTERNAL + INTERNAL_AUDIT (APROBADO_INTERNO)
- [ ] Chat (F22) — fuera de alcance
- [ ] Paneles backtest/optimizer (F21) — fuera de alcance
- [ ] `FASE_20_APPROVED.md` formal externo — pendiente Meta-Auditor externo

## Fuera de alcance F20

Chat completo (F22), paneles de todas las features (F21), Electron, LIVE UI arming.

## Auditoría INTERNAL (2026-07-26)

| Check | Resultado |
|-------|-----------|
| Bind loopback default | PASS |
| LIVE mode rejected (API + CLI) | PASS |
| PaperBroker path (connect + submit) | PASS |
| `LIVE_BLOCKED is True` | PASS |
| Entry `quantlab-workbench` | PASS |
| SPA `wm.js` WindowManager | PASS |
| mypy / ruff / pytest workbench / health | PASS |
