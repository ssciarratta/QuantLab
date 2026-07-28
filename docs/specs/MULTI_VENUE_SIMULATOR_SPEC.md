# Spec — Simulador multi-venue (histórico spot/futuros + leverage)

**Versión:** 0.1 (borrador implementación)  
**Fecha:** 2026-07-28  
**Estado:** EN CURSO — sin certificado de fase

## Objetivo

Responder en una sola corrida:

> “Si corría la estrategia X en **OKX futuros BTC a 10x** con capital Y, ¿qué hubiera pasado?”  
> Y comparar lado a lado con **Binance / Bybit / Hyperliquid**, spot o futuros, distintas x.

## Decisiones de producto (APROBADAS)

| Tema | Decisión |
|------|----------|
| Exchanges | Binance, OKX, Bybit, Hyperliquid — los 4 pre-marcados |
| Comparación | Tabla lado a lado en una corrida |
| Spot vs futuros | Uno u otro por corrida (no ambos a la vez) |
| Futuros | USDT-margined / perpetuos |
| Leverage | Modelo **PnL × x** sobre capital fijo (mismo margen inicial) |
| Leverage UI | Slider 1–125 + corrida multi-x opcional |
| Liquidación | Simular cierre — **checkbox** para apagar |
| Funding | Histórico en perps — **checkbox** para apagar |
| Mercados | Manual, hasta ~5, mapeo automático del subyacente |
| Tiempo | Últimas N velas, intervalo 1m–1d |
| Capital | Configurable en UI |
| Fees | Tabla por venue |
| Estrategias | Catálogo completo, mismos parámetros |
| Resultados | Tabla resumen + tarjetas detalle |
| UI | **Panel nuevo “Simulador”** |
| Modo | Toggle histórico vs paper (sin live real) |

## Arquitectura (v1)

```
Panel Simulador (JS)
  → POST /api/lab/sim/compare
    → multi_venue_sim.run_compare()
      → symbol_map.resolve(underlying, venue, market_type)
      → public_md.fetch_klines (por venue)
      → run_lab_backtest (motor 1x spot)
      → leverage_overlay.apply()  # PnL×L, liq, funding toggles
      → filas SimCompareRow
```

## Fases de entrega

| Fase | Entrega | Estado |
|------|---------|--------|
| 0 | Esta spec + manual `35-simulador.md` | EN CURSO |
| 1 | `research/sim/` leverage + liq + funding + tests | EN CURSO |
| 2 | MD público: Binance futuros, OKX, Bybit, HL | PENDIENTE |
| 3 | API `/api/lab/sim/compare` | PENDIENTE |
| 4 | Panel UI + tabla | PENDIENTE |
| 5 | Fees por venue + export Reports | PENDIENTE |

## Invariantes

- `LIVE_BLOCKED=True` — sin routing venue
- MD público sin API keys cuando aplique
- Investigación — no promete rentabilidad
