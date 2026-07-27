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
- Routing F101: fills **simulados locales** vía `/api/live/demo/submit` (post-unlock).
- MD público Binance disponible. Testnet HMAC remoto: fase siguiente con keys en env.

## Binance demo

Solo usá keys de **demo/testnet** en env locales cuando la fase de routing remoto lo pida.
Nunca pegues secrets al agente ni al repo.
