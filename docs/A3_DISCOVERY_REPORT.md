# A3 Discovery Report — QuantLab Fase 3

**Fecha de verificación:** 2026-07-24  
**Librería:** `pyrofex` / import `pyRofex`  
**Versión fijada:** `0.5.0` (PyPI / `uv.lock`)  
**Python del proyecto:** `>=3.11`  
**Entorno de inspección:** Windows, CPython 3.12, `uv sync --frozen`

---

## 1. Resumen ejecutivo

`pyRofex` 0.5.0 es el conector oficial hacia la API Primary / Matba Rofex (hoy A3 Mercados).
Expone REST + WebSocket para market data, instrumentos, historial de trades, órdenes,
cuenta y posiciones.

**Hallazgo crítico para QuantLab:** la librería entrega **trades históricos**, no velas OHLC
canónicas. Las barras deben construirse en QuantLab de forma determinista y versionada.

**Hallazgo de naming:** el enum de simulación es `Environment.REMARKET` (no "simulation")
y producción es `Environment.LIVE` (no "production"). QuantLab usará nombres propios
(`simulation` / `production`) y un mapper explícito.

---

## 2. Environments verificados

| Enum pyRofex | Valor | Rol QuantLab |
|--------------|-------|--------------|
| `Environment.REMARKET` | `1` | `simulation` (reMarkets) |
| `Environment.LIVE` | `2` | `production` (bloqueado) |

Inicialización pública:

```text
pyRofex.initialize(user, password, account, environment, proxies=None, ssl_opt=None, active_token=None)
```

---

## 3. Capacidades REST verificadas (API pública)

| Función | Uso Fase 3 |
|---------|------------|
| `get_segments` | Segmentos de mercado |
| `get_all_instruments` | Instrument master |
| `get_instruments` | Filtro por CFI / segmento |
| `get_detailed_instruments` | Detalle masivo |
| `get_instrument_details` | Detalle por ticker |
| `get_market_data` | Snapshot (bids/offers/last/…) |
| `get_trade_history` | Trades históricos |
| `send_order` | Órdenes (solo simulation en F3) |
| `cancel_order` | Cancelación |
| `get_order_status` / `get_all_orders_status` | Estado |
| `get_account_position` / `get_detailed_position` | Posiciones |
| `get_account_report` | Cuenta |

---

## 4. Capacidades WebSocket verificadas

| Función | Rol |
|---------|-----|
| `init_websocket_connection` | Conexión + handlers |
| `close_websocket_connection` | Cierre |
| `market_data_subscription` | MD |
| `order_report_subscription` | Execution reports |
| `add_websocket_market_data_handler` | Callback MD |
| `add_websocket_order_report_handler` | Callback órdenes |
| `add_websocket_error_handler` | Errores |
| `send_order_via_websocket` / `cancel_order_via_websocket` | Alternativa WS |

**Política QuantLab:** el callback solo encola; el procesamiento pesado es fuera del hilo WS.

---

## 5. Enums relevantes

- **Market:** `ROFEX` → wire `'ROFX'`
- **Side:** `BUY`/`SELL` → `'buy'`/`'sell'`
- **OrderType:** `LIMIT`, `MARKET`, `MARKET_TO_LIMIT`
- **TimeInForce:** `DAY`, `IOC`, `FOK`, `GTD`
- **MarketDataEntry:** BIDS, OFFERS, LAST, OPEN/CLOSE/SETTLEMENT, HIGH/LOW, TRADE_VOLUME, OPEN_INTEREST, …
- **MarketSegment:** DDF, DDA, DUAL, U_*, MERV
- **CFICode:** STOCK, BOND, FUTURE, opciones, CEDEAR, …

---

## 6. Formato de instrumentos / trades (observado en docs + firma)

- Instrumentos: listados via REST; detalle incluye ticker, mercado, CFI, segmentos.
- Trades históricos: `get_trade_history(ticker, start_date, end_date, market=ROFEX)`.
- Market data: `get_market_data(ticker, entries=None, depth=1, market=ROFEX)`.

Los payloads exactos se capturan como **raw JSON append-only**; el dominio solo ve DTOs mapeados.

---

## 7. Limitaciones conocidas

1. **Sin OHLCV nativo** → QuantLab construye barras desde trades.
2. **API global mutable** (`pyRofex.initialize` / módulo service) → encapsular en clientes de sesión; no esparcir estado global.
3. **Métodos privados** `_set_environment_parameter(s)` existen en `service` → **no usar** salvo necesidad documentada (deuda).
4. **Dependencia websocket-client:** docs históricas citan 0.54–0.57; `uv` resolvió `websocket-client==1.9.0` con `pyrofex==0.5.0`. Verificar comportamiento WS en simulation; registrar divergencia.
5. **Docs oficiales** viven en Primary API Hub (`apihub.primary.com.ar`); nombres Matba Rofex / Primary / A3 coexisten.
6. Rate limits: no fijados de forma clara en la librería; aplicar backoff y métricas propias.

---

## 8. Naming: A3 / Primary / Matba Rofex

| Nombre | Contexto |
|--------|----------|
| A3 Mercados | Marca / mercado actual (futuros AR) |
| Matba Rofex | Nombre histórico del exchange |
| Primary | Plataforma API / hub |
| ROFEX / ROFX | Código de mercado en wire |
| reMarkets | Entorno de simulación (`REMARKET`) |

QuantLab habla de **A3** en docs de producto y **provider=`a3`** en paths/manifests.

---

## 9. Riesgos de producción

- `Environment.LIVE` + credenciales reales = órdenes reales.
- Fase 3: producción **bloqueada** por gates múltiples + kill switch.
- CI: `QUANTLAB_ENABLE_LIVE_TRADING=DISABLED`.
- No hay tests automáticos de trading en LIVE.

---

## 10. Datos no disponibles directamente

- Barras OHLC canónicas del exchange (construir).
- Features / order book histórico completo a largo plazo (fuera de alcance F3 salvo capture live).
- Garantía de bit-a-bit cross-environment (DEC-022).

---

## 11. Adaptación al dominio QuantLab

| Externo | Dominio |
|---------|---------|
| ticker ROFX | `Instrument.symbol` + `metadata` original |
| trade history | `Trade` + raw record |
| OHLC construido | `Bar` + DatasetManifest |
| send_order | `OrderIntent` → risk gate → adapter |
| order report WS | `ExecutionReport` / audit log |

**Regla:** `quantlab.core` y el resto del dominio **no importan** `pyRofex`.

---

## 12. Fuentes consultadas

- Paquete instalado `pyRofex` 0.5.0 (introspección de firmas/enums)
- PyPI `pyrofex` 0.5.0
- GitHub `matbarofex/pyRofex` (descripción pública)
- Primary API Hub (referencia documental)
- Arquitectura QuantLab v1.1 (`docs/Arquitectura.md`)

---

*Documento vivo de Fase 3. Actualizar si cambia la versión de pyRofex o el comportamiento verificado en reMarkets.*
