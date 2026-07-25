# A3 Integration Design — QuantLab

**Versión:** 1.0  
**Fecha:** 2026-07-24  
**Dependencia:** `pyRofex==0.5.0`  
**Discovery:** [A3_DISCOVERY_REPORT.md](A3_DISCOVERY_REPORT.md)

---

## 1. Arquitectura

```text
┌─────────────────────────────────────────────────────────────┐
│ quantlab.core (dominio) — NO importa pyRofex                │
│ Instrument, Trade, Bar, OrderIntent, Manifests, …           │
└────────────────────────────▲────────────────────────────────┘
                             │ mappers
┌────────────────────────────┴────────────────────────────────┐
│ quantlab.data                                               │
│  catalog | storage | quality | normalization | replay       │
│  exchanges.a3  ← anticorrupción                             │
│    client (REST/WS wrap) | models DTO | mappers | persistence│
└────────────────────────────▲────────────────────────────────┘
                             │
                       pyRofex 0.5.0
                             │
                    remarkets / LIVE API
```

### Límites de responsabilidad

| Componente | Hace | No hace |
|------------|------|---------|
| `A3MarketDataClient` | instrumentos, MD, trades, WS MD | órdenes |
| `A3ExecutionClient` | órdenes, cancel, status, cuenta | normalización de barras |
| `A3Adapter` | fachada + gates | lógica de dominio |
| Data Layer | raw/processed/catalog/quality | trading |
| Strategy | `OrderIntent` | llamar pyRofex |

---

## 2. Planes

### Data Plane (aprobación normal F3)
Ingesta → raw append-only → normalización → quality → processed + manifest → catálogo → replay.

### Execution Plane (simulation)
`OrderIntent` → risk gate → kill switch → allowlists → `A3ExecutionClient` → reMarkets → reconcile.

### Production order routing
**BLOQUEADO** por defecto. Requiere todos los gates (ver §8 PROMPT / A3_SECURITY).

---

## 3. Configuración

- Archivo: `config/exchanges/a3.yaml` (sin secretos)
- Credenciales: env `QUANTLAB_A3_USER|PASSWORD|ACCOUNT|TOKEN`
- Live kill: `QUANTLAB_ENABLE_LIVE_TRADING` (default disabled)

Mapper de environment:

| QuantLab | pyRofex |
|----------|---------|
| `simulation` | `Environment.REMARKET` |
| `production` | `Environment.LIVE` |

---

## 4. Persistencia

```text
data/raw/a3/YYYY-MM-DD/{SYMBOL_SAFE}/...
data/processed/a3/{dataset}/schema_v{N}/...
```

- Raw: JSONL append-only + checksum + ingestion_run_id
- Processed: Parquet (DEC-002) + DatasetManifest schema_version
- Catálogo: SQLite local determinista (fallback DEC-003; DuckDB opcional post-F3 si hace falta)

---

## 5. Barras desde trades

Timeframes: `1m,5m,15m,30m,1h,1d`  
Reglas: timezone-aware, intervalo half-open `[start, end)`, Decimal, dedupe explícita, gaps registrados, barra final incompleta marcada.

---

## 6. WebSocket

Callback → cola acotada → worker → raw + métricas.  
Reconexión con backoff. Backpressure: drop + contador `dropped_messages`.

---

## 7. Idempotencia / reconciliación

- `client_order_id` estable por intención
- Antes de reenviar: `get_order_status` / listado por client id
- Cancel: confirmar estado terminal (no solo ACK REST)

---

## 8. Risk gate + kill switch

`PreTradeRiskGate.evaluate(intent, context) -> RiskDecision`  
Kill switch persistente en `data/runtime/kill_switch.json` (bloquea LIVE por defecto).

---

## 9. Tests

| Categoría | Gate |
|-----------|------|
| Offline | siempre CI |
| Simulation | `QUANTLAB_RUN_A3_SIMULATION_TESTS=1` |
| Production RO | manual |
| Production trading | **no automático F3** |

---

## 10. Matriz de implementación

| Entregable | Archivos | Dependencias | Tests | Riesgo | Estado |
| ---------- | -------- | ------------ | ----- | ------ | ------ |
| Discovery | `docs/A3_DISCOVERY_REPORT.md` | — | n/a | bajo | DONE |
| Diseño | `docs/A3_INTEGRATION.md` | discovery | n/a | bajo | DONE |
| Config A3 | `config/exchanges/a3.yaml`, `.env.example` | infra config | unit | medio | WIP |
| Excepciones A3 | `data/exchanges/a3/exceptions.py` | core | unit | bajo | WIP |
| DTOs + mappers | `models.py`, `mappers.py` | core types | unit | medio | WIP |
| Raw/processed storage | `data/storage/` | pathlib | unit | medio | WIP |
| Quality | `data/quality/` | core | unit | medio | WIP |
| Bars from trades | `data/normalization/bars.py` | Trade/Bar | unit | alto | WIP |
| Catalog | `data/catalog/` | manifests | unit | medio | WIP |
| REST client | `a3/client.py` | pyRofex wrap | fake | alto | WIP |
| Adapter + gates | `a3/adapter.py`, risk | OrderIntent | unit | crítico | WIP |
| WS capture | `a3/websocket.py` | queue | unit fake | alto | WIP |
| Execution sim | execution client | remärkets | optional | crítico | WIP |
| CLI | entry points | adapter | smoke | medio | WIP |
| Docs operativas | `docs/A3_*.md` | — | n/a | bajo | WIP |
| Review Package F03 | scripts | F2 generator | CI | medio | pending |

---

## 11. Decisiones (a registrar)

- DEC-040 — Adaptador anticorrupción A3 / dominio sin pyRofex
- DEC-041 — Separación Data Plane / Execution Plane
- DEC-042 — Producción bloqueada por múltiples gates
- DEC-043 — Barras OHLCV construidas desde trades
- DEC-044 — Raw append-only

Ver `learning/decisiones.txt`.
