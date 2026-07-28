# Manual — Simulador multi-venue

Panel nuevo con solapas: Aprender · Histórico · Estrés · Practicar · Estrategias.

## Cómo abrir

1. Menú **QL** → **Simulador**
2. Ctrl+K → `simulador`

## Controles comunes (todas las solapas)

- Spot o Futuros
- Leverage 1–125 (o multi-x 1/2/5/10)
- Período (1d…1 año) + intervalo Binance completo
- Contador **≈ N velas**
- Capital inicial + inversión por trade (validación sizing)
- Fees preset por venue (editables) + **+ Gasto**
- Benchmark tasa anual USD (se temporaliza al período)
- Toggles: liquidación · funding

## Solapas

| Solapa | Uso |
|--------|-----|
| Aprender | Backtest datos inventados |
| Histórico | Comparar Binance/OKX/Bybit/HL |
| Estrés | Abre Monte Carlo |
| Practicar | Guided Lab / Paper Blotter |
| Estrategias | Catálogo + tipo de corrida |

## API

- `GET /api/lab/sim/fees`
- `GET /api/lab/sim/period?period_days=&interval=`
- `POST /api/lab/sim/compare`
- `POST /api/lab/sim/sizing`

## Fees (importante)

Los presets/edits de maker/taker bps van en **metadata** de la comparación.
El motor de fills del backtest lab sigue usando **Binance Spot VIP0** (v1).
Los gastos custom (`+ Gasto`) sí restan del equity del overlay.

## Invariantes

- `LIVE_BLOCKED=True` · research-safe · sin órdenes live
