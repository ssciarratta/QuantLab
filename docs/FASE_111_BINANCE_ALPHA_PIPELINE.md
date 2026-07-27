# FASE 111 — Binance alpha real + pipeline scan→backtest + Chat copilot

**Versión:** 1.01.0  
**Estado:** INTERNAL (sin certificado APROBADO)

## Objetivo

Cerrar gaps del Guided Lab Binance:

1. Ranking alpha sobre klines reales (MD público read-only)
2. Backtest automático top-N del scan (pipeline)
3. Chat IA con guía operativa (chips + tools nuevas)

## API nuevas

| Ruta | Descripción |
|------|-------------|
| `POST /api/lab/binance/scanner` | AlphaScanner sobre klines USDT |
| `POST /api/lab/binance/pipeline` | Scanner + backtest batch top-N |

## UI Guided Lab

- **Ranking alpha Binance** → `/api/lab/binance/scanner`
- **Backtest top 5 Binance** → `/api/lab/binance/pipeline`

## Chat IA

Tools: `explain_guided_lab`, `explain_binance_lab`, `suggest_workflow`  
Chips rápidos en panel Chat IA.

## Invariantes

- `LIVE_BLOCKED=True`
- Sin API keys para MD público
- Chat no envía órdenes

## Doc operador

`docs/GUIA_COMPLETA_QUANTLAB.md`
