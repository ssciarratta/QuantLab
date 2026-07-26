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
- Routing venue real de órdenes: aún stub (próxima fase). MD público Binance sí disponible.

## Binance demo

Solo usá keys de **demo/testnet** en env locales cuando la fase de routing lo pida.
Nunca pegues secrets al agente ni al repo.
