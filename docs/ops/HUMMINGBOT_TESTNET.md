# Hummingbot + QuantLab — Testnet / Paper

## Principio de desacoplamiento

QuantLab investiga; Hummingbot ejecuta (proceso **externo**). QuantLab:

- Exporta configuración (`HummingbotExporter`, panel *Hummingbot Export*).
- Detecta si Hummingbot está instalado (`hummingbot_probe.py`).
- **No** rutea órdenes a HB automáticamente.
- **No** habilita trading real.

## Conectores relevantes (2026)

| Objetivo | Connector Hummingbot | Notas |
|----------|---------------------|-------|
| Spot paper (HB) | `binance_paper_trade` | MD real, fills simulados en HB |
| Perp testnet | `binance_perpetual_testnet` | Futures testnet |
| Spot testnet API | **No disponible en HB** | Usar QuantLab F102 (`testnet.binance.vision`) |

## Instalación Windows (recomendado)

1. WSL2 + Ubuntu: `wsl --install -d Ubuntu`
2. Docker Desktop con integración WSL2
3. Clonar/instalar Hummingbot según docs oficiales
4. Montar `conf/` en volumen persistente

Script guía: `tools/windows/05_install_or_setup_hummingbot.bat`

## Verificación sin órdenes

En Hummingbot (externo):

```text
connect binance_paper_trade
balance
status
```

En QuantLab:

```bash
uv run quantlab-testnet hummingbot
uv run quantlab-testnet hb-verify
```

## Export desde QuantLab

El payload incluye:

- `live_routing: false`, `blocked: true`
- `environment: testnet_spot_quantlab`
- `recommended_hb_connectors` (paper / perp testnet / F102 nativo)

Operador: copiar parámetros del export a config HB manualmente o vía script propio.

## Seguridad

- `hb-verify` escanea configs locales buscando `api.binance.com` o connector spot mainnet.
- Nunca commitear `conf/connectors/*.yml` con keys reales.
