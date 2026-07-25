# A3 Runbook

## Configuración
1. Copiar `.env.example` → `.env` (nunca commitear).
2. Revisar `config/exchanges/a3.yaml` (`environment: simulation`).
3. `uv sync --frozen --extra dev`

## Health / instrumentos (offline)
```bash
uv run quantlab-a3 health
uv run quantlab-a3 instruments
```

## Con API real (reMarkets)
```bash
uv run quantlab-a3 --live-api health
```

## Captura histórica offline (fake)
```bash
uv run quantlab-a3 historical DLR/DIC24 --timeframe 1m
```

## Kill switch
Archivo: `data/runtime/kill_switch.json`  
Default: `block_production=true`. No se reactiva al reiniciar el proceso.

## Errores frecuentes
- Faltan env vars → `A3ConfigurationError`
- Orden en production → `A3LiveTradingDisabledError`
- Risk → `A3RiskRejectedError`
