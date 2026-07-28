# Spec UX — Solapas QuantLab (investigación + capital + fees + benchmark)

**Actualizado:** 2026-07-28  
**Estado:** diseño aprobado en conversación (sin implementación completa)

## Solapas (todas mantienen spot/futuros + leverage + período + intervalo Binance)

| # | Solapa | Qué hace |
|---|--------|----------|
| 1 | **Aprender** | Backtest con datos **inventados** (lab). Misma lógica de capital/fees/x. |
| 2 | **Histórico** | Mercados reales + comparación multi-exchange. |
| 3 | **Estrés** | Monte Carlo sobre un resultado previo. |
| 4 | **Practicar** | Órdenes paper / demo / A3 (no horizonte de meses). |
| 5 | **Estrategias** | Catálogo completo; al elegir una, se ve qué tipo de corrida permite. |

Controles **comunes en todas** (bloque fijo):

1. Modo: Spot | Futuros (USDT perp)  
2. Leverage: slider 1–125 (+ multi-x opcional)  
3. Período: presets + personalizado (**igual en todas**)  
4. Intervalo: **todas las temporalidades Binance**  
5. Contador live: `≈ N velas`  
6. **Capital inicial** (obligatorio)  
7. **Inversión por trade** (obligatorio; validado vs exchange)  
8. **Fees / gastos** (presets por venue + editables + agregar más)  
9. **Benchmark** tasa anual USD (manual) → retorno del período testeado  

## Solapa Estrategias

- Lista todas del catálogo (runnable + stub).  
- Al seleccionar:  
  - nombre, familia, descripción  
  - **tipo de corrida**: inventado / histórico / estrés / práctica  
  - parámetros default  
  - badge `runnable` vs `stub`  
- Botón: “Usar en Aprender / Histórico / …” → prellena estrategia en esa solapa.

## Capital y tamaño por trade (siempre)

Campos obligatorios en **toda** corrida:

| Campo | Ejemplo | Validación |
|-------|---------|------------|
| Capital con el que entro | 10.000 USDT | > 0 |
| Invierto por trade | 500 USDT o 5% del capital | ≤ capital; en futuros: notional = margen × leverage ≤ reglas venue |
| Confirmación exchange | min notional, step size, max leverage del símbolo | Fail-closed si no cumple |

Mensaje UI ejemplo:  
`OKX BTC-USDT-SWAP @ 10x: margen 500 → notional 5.000 · min notional OK ✓`

## Fees y gastos

### Presets investigados (VIP0 / retail base — verificar al implementar)

| Venue | Spot maker/taker | Futuros maker/taker | Otros variables |
|-------|------------------|---------------------|-----------------|
| Binance | 0.10% / 0.10% (BNB −25% → 0.075%) | 0.02% / 0.05% | Funding ~8h; retiro red |
| OKX | tip. ~0.08–0.10% retail | 0.02% / 0.05% | Funding; OKB discount |
| Bybit | tip. spot retail | 0.02% / 0.055% | Funding ~8h |
| Hyperliquid | spot ~0.04% / 0.07% | 0.015% / 0.045% | Funding horario; retiro ~1 USDC |

**Fijos vs variables (modelo de costo):**

- **Variables %**: maker, taker (sobre notional)  
- **Variables periódico**: funding (solo futuros; toggle)  
- **Fijos / custom**: retiro, gas, “otro gasto” (USD o %); botón **+ Agregar gasto**  
- Todo editable; preset se carga al elegir exchange y el usuario puede override.

## Benchmark (obligatorio en toda evaluación)

- Input: **tasa anual en USD** (ej. 5% = tasa “sin riesgo” / bench a mano).  
- Se **temporaliza** al horizonte exacto del test:

```
retorno_bench = capital × ((1 + tasa_anual)^(días/365) − 1)
```

Aprox. lineal corta (opcional UI): `capital × tasa_anual × (horas / (365×24))`

Ejemplo: capital 10.000, bench 5% anual, test **2 horas**:

```
bench_2h ≈ 10000 × 0.05 × (2 / 8760) ≈ 0.114 USDT
```

En resultados siempre mostrar:

| Métrica estrategia | Bench del mismo período | Exceso (alpha vs bench) |
|--------------------|-------------------------|-------------------------|

## Intervalos Binance (todas las solapas)

`1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M`

UI: período + intervalo → `≈ N velas` siempre visible.

## Invariantes

- LIVE_BLOCKED; research-safe  
- Fees de exchange = presets documentados, no “VIP inventada vía API”  
- Benchmark no es predicción: es **alternativa pasiva** del mismo capital/tiempo  
