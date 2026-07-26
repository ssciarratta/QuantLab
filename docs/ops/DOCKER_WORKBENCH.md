# Workbench Docker (opt-in) — Fase 53

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
docker build -f Dockerfile.workbench -t quantlab-workbench:0.45.0 .
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

## Health check rápido

```bash
curl -sS http://127.0.0.1:8765/api/health
# ok=true · live_blocked=true
```

Apagado ordenado (F52): `docker stop` envía SIGTERM → graceful shutdown.

## Qué no hace esta imagen

- No flips `LIVE_BLOCKED`
- No auth WAN / TLS / reverse-proxy
- No incluye `.env` ni credenciales (pasalas solo si vos las montás conscientemente)
- Build de imagen **no** es requisito de CI; los tests F53 parsean el Dockerfile sin `docker build`

## Referencias

- Spec: `docs/FASE_53_DOCKER.md`
- 1-click nativo (sin Docker): `docs/ops/WORKBENCH_1CLICK.md`
- Bind non-loopback (F25): flag `--allow-non-loopback`
