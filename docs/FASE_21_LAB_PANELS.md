# Fase 21 — Paneles lab del Workbench

**Estado:** IMPLEMENTADO (v0.13.0)  
**Prerrequisito:** F20 Workbench (v0.12.0)  
**Alcance:** paneles + API `/api/lab/*` para funcionalidades principales del laboratorio.

## Objetivo

Usar con mouse (ventanas MDI) las features de research sin credenciales ni LIVE:

1. Backtest bar-based (dummy / momentum / buy_once sobre sintéticos)
2. Alpha Scanner
3. Metrics / último resultado de sesión
4. Experiment Registry (listar, tmp)
5. Optimizer grid (mini)
6. Monte Carlo (mini)
7. Features pipeline demo
8. Hummingbot export (validate/build, path-safe, `live_routing: false`)
9. Validation splits info
10. Health / Mode / MD / Blotter — en menú Inicio (F20)

## Stack

Extiende F20 (`stdlib http.server` + SPA):

```text
src/quantlab/workbench/
├── lab_services.py    # adapters thin → módulos existentes
├── api.py             # handlers /api/lab/*
├── server.py          # rutas GET/POST lab
└── static/js/panes/   # backtest, scanner, metrics, …
```

## API lab

| Método | Ruta | Notas |
|--------|------|-------|
| GET | `/api/lab/capabilities` | features + strategies |
| POST | `/api/lab/backtest` | `strategy_id` + params → metrics summary |
| POST | `/api/lab/scanner` | ranking sintético |
| GET | `/api/lab/experiments` | registry sesión (demo draft) |
| POST | `/api/lab/optimize` | grid lookback×qty (≤12) |
| POST | `/api/lab/montecarlo` | N∈[2,20] |
| POST | `/api/lab/features` | close + simple_return |
| POST | `/api/lab/export-hb` | sandbox tmp; rechaza path externo |
| GET | `/api/lab/metrics` | último `last_lab_result` |
| GET | `/api/lab/validation` | train/val/OOS + walk-forward |

Todas las respuestas incluyen `live_routing: false` (o equivalente). Nunca `place_order` live.

## UI

Menú Inicio agrupado: **Sesión** (Health/MD/Blotter) + **Laboratorio** (9 paneles).  
Cada pane llama a `QLApi.lab*` y muestra JSON tipado.

## Seguridad

- Datos sintéticos en memoria / tmp de sesión
- Export HB solo bajo sandbox; `HummingbotExporter.LIVE_BLOCKED`
- `OperatingMode.LIVE` → 400; `LIVE_BLOCKED is True` sin flip
- Sin chat (F22)

## Definition of Done

- [x] `lab_services.py` thin adapters sobre código existente
- [x] Endpoints `/api/lab/*` + wiring en `server.py`
- [x] Paneles JS + launcher
- [x] Tests `tests/unit/workbench/test_lab_api.py` (happy-path + LIVE bloqueado)
- [x] Version 0.13.0
- [x] Docs DoD + implementation report
- [x] QA: ruff / mypy --strict / pytest workbench / quantlab-health

## Fuera de alcance

Chat IA (F22), Electron, flip LIVE, datos reales con credenciales.
