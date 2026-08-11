# Testnet Strategy Execution — Estado MVP

Actualizado: 2026-08-10

## Alcance Fase A–O (implementado)

- Registro de capacidades por estrategia (`StrategyExecutionRegistry`)
- Manifiesto versionado (`StrategyPromotionManifest`) con hashes
- Persistencia local `{session_root}/execution/`
- API HTTP `/api/execution/*`
- Panel UI **Probar estrategia (testnet)** — promoción → validar → preflight → sesión
- **Paso 5 — corrida PAPER real** (`start-paper`) con PaperSessionRunner
- Historial sesiones ejecución en el panel (`GET /api/execution/sessions`)
- Handoffs: Alpha Scanner · Simulador
- Preflight **nunca** habilita órdenes testnet remotas (`remote_orders_enabled=false`)
- `MAX_ACTIVE_STRATEGIES=1` para sesiones RUNNING

## Certificación MVP

| Estrategia | PAPER | Spot TN | Futures TN |
|------------|-------|---------|------------|
| buy_once   | sí    | sí      | no         |
| dummy, momentum | sí | no | no |
| resto      | paper/research según catálogo | no | no |

## Pendiente (no iniciar sin autorización)

- Fase P: primera orden Spot Testnet remota
- Fase Q: Futures Testnet vía Hummingbot IPC
- Fase R: estrategia limitada en testnet
- Hot reload parámetros en runtime
- Certificación estrategia por estrategia

## Endpoints

```
GET  /api/execution/strategies
GET  /api/execution/strategies/{id}/capabilities
POST /api/execution/promotions
GET  /api/execution/promotions/{id}
POST /api/execution/promotions/{id}/validate
POST /api/execution/promotions/{id}/preflight
POST /api/execution/promotions/{id}/open-session
POST /api/execution/sessions/{id}/start-paper
GET  /api/execution/sessions
GET  /api/execution/sessions/{id}/status
POST /api/execution/sessions/{id}/stop
GET  /api/execution/hummingbot/status
```

## Invariantes

- `LIVE_BLOCKED=True`
- Spot Testnet órdenes: QuantLab nativo (no connector HB spot testnet)
- Futures Testnet: Hummingbot `binance_perpetual_testnet` (deploy pendiente)
