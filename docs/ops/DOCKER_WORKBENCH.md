# Workbench Docker (opt-in) — Fase 53 (+ probes F54)

Imagen **opt-in** del QuantLab Workbench para Docker Desktop / local.
**LIVE sigue bloqueado** (`LIVE_BLOCKED=True`). Sin auth HTTP.

## Riesgo (leer antes de publicar puertos)

El `CMD` del `Dockerfile.workbench` usa:

```text
quantlab-workbench --host 0.0.0.0 --allow-non-loopback --no-browser
```

- `--allow-non-loopback` + bind `0.0.0.0` es **necesario** para que el port-map de Docker Desktop funcione (el proceso escucha en la interfaz del contenedor, no en el loopback del host).
- **No hay autenticación HTTP.** No publicar el puerto a WAN ni a `0.0.0.0` en el host.
- Publicá **solo** en loopback del host: `-p 127.0.0.1:8765:8765`.

## Build

Desde la raíz del repo:

```bash
docker build -f Dockerfile.workbench -t quantlab-workbench:0.49.0 .
# o tag local corto:
docker build -f Dockerfile.workbench -t quantlab-workbench .
```

`.dockerignore` excluye `.env`, `data/`, secrets, venvs, tests y docs pesados.

## Run (loopback-only publish)

```bash
docker run --rm -p 127.0.0.1:8765:8765 quantlab-workbench
```

Abrí en el host: [http://127.0.0.1:8765](http://127.0.0.1:8765)

Opcional — montar sesión durable en el host:

```bash
mkdir -p "$PWD/data/runtime"
docker run --rm \
  -p 127.0.0.1:8765:8765 \
  -v "$PWD/data/runtime:/app/data/runtime" \
  quantlab-workbench
```

## Healthcheck / probes (F54)

Preferí los probes delgados frente a `/api/health` para Docker / orchestrators:

| Endpoint | Uso | Status |
|----------|-----|--------|
| `GET /api/livez` | **Liveness** — proceso up | siempre **200** si responde |
| `GET /api/readyz` | **Readiness** — LIVE bloqueado + session root writable | **200** ready / **503** not ready |
| `GET /api/health` | Health report rico (compat) | 200 + JSON detallado |

```bash
# Liveness
curl -sS http://127.0.0.1:8765/api/livez
# {"ok":true,"alive":true,"status":"alive",...,"live_blocked":true}

# Readiness
curl -sS -w "\nHTTP %{http_code}\n" http://127.0.0.1:8765/api/readyz
# 200 → ready; 503 → not_ready (checks.live_blocked / session_root_writable)

# Compat
curl -sS http://127.0.0.1:8765/api/health
# ok=true · live_blocked=true
```

Ejemplo `HEALTHCHECK` (liveness; el `Dockerfile.workbench` base no lo fija — opt-in):

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/livez')"
```

Para readiness en compose/orchestrator, usá `/api/readyz` (exit non-zero si HTTP ≠ 200).

Apagado ordenado (F52): `docker stop` envía SIGTERM → graceful shutdown.

## Qué no hace esta imagen

- No flips `LIVE_BLOCKED`
- No auth WAN / TLS / reverse-proxy
- No incluye `.env` ni credenciales (pasalas solo si vos las montás conscientemente)
- Build de imagen **no** es requisito de CI; los tests F53 parsean el Dockerfile sin `docker build`

## Referencias

- Spec F53: `docs/FASE_53_DOCKER.md`
- Spec F54 probes: `docs/FASE_54_PROBES.md`
- 1-click nativo (sin Docker): `docs/ops/WORKBENCH_1CLICK.md`
- Bind non-loopback (F25): flag `--allow-non-loopback`
