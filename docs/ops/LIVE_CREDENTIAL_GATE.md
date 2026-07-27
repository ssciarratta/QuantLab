# LIVE Credential Gate (F100)

## Modelo

- `LIVE_BLOCKED=True` permanece como default.
- LIVE solo se habilita con **unlock de sesión** vía usuario/contraseña.
- Credenciales locales del operador (nunca en git):

```bash
set QUANTLAB_LIVE_USER=tu_usuario
set QUANTLAB_LIVE_PASSWORD=tu_password
```

- Endpoints: `GET /api/live/status`, `POST /api/live/unlock`, `POST /api/live/lock`
- Password **no** se persiste ni se escribe en activity log.
- Scope inicial: `binance_demo`.
- Routing F101/F102: default fills **simulados locales** vía `/api/live/demo/submit`.
- Testnet remoto opt-in: `QUANTLAB_DEMO_USE_TESTNET=1` + `BINANCE_DEMO_API_KEY` /
  `BINANCE_DEMO_API_SECRET` (nunca en git). Rechaza producción.

## Binance demo

```bash
set QUANTLAB_LIVE_USER=tu_usuario
set QUANTLAB_LIVE_PASSWORD=tu_password
rem opcional testnet:
set QUANTLAB_DEMO_USE_TESTNET=1
set BINANCE_DEMO_API_KEY=...
set BINANCE_DEMO_API_SECRET=...
```

Nunca pegues secrets al agente ni al repo.
