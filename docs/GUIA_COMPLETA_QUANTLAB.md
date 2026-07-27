# Guía completa QuantLab v1.00+ — Para operadores e IAs

**Propósito:** documento autocontenido para copiar a otra IA y que guíe al usuario en operación diaria.  
**Repo:** QuantLab · laboratorio cuantitativo (NO bot de trading automático).  
**UI:** Workbench loopback `http://127.0.0.1:8765`  
**Versión referencia:** 1.00.0 · F19–F110 INTERNAL

---

## 1. Qué es QuantLab

QuantLab es un **laboratorio de investigación cuantitativa**. Permite:

- Simular estrategias (backtest) antes de operar
- Escanear mercados (sintético o Binance MD público)
- Operar en **paper** (fills simulados, journal durable)
- Camino **LIVE gated** para demo Binance (unlock humano; testnet opt-in)
- Integración **A3 reMarkets** (MD read-only + paper; sin routing venue por defecto)

**NO es:** un bot que opera solo, HFT producción, ni asesor financiero.

---

## 2. Invariantes de seguridad (irrenunciables)

| Regla | Significado |
|-------|-------------|
| `LIVE_BLOCKED=True` | Sin unlock, routing LIVE bloqueado |
| `REAL = PAPER` | Modo REAL del producto = paper fills, no venue |
| Unlock LIVE | Solo con `QUANTLAB_LIVE_USER` + `QUANTLAB_LIVE_PASSWORD` en env local |
| Secrets | Nunca en git, logs ni chat audit |
| Binance prod | `api.binance.com` rechazado para **órdenes**; MD público read-only permitido |
| Testnet | Solo con `QUANTLAB_DEMO_USE_TESTNET=1` + `BINANCE_DEMO_*` |
| A3 venue | Fills = PaperBroker; MD env opt-in con `QUANTLAB_A3_MD_READONLY=1` |
| Chat IA | Safe-mode: **no envía órdenes**; solo lectura/explicación |

---

## 3. Cómo arrancar

```bash
cd C:\Users\ssciarratta\Desktop\QuantLab   # o ruta del clone
uv sync --extra dev                         # primera vez
set -a && source .env && set +a             # Git Bash, si hay .env
uv run quantlab-workbench                   # abre browser o ir a :8765
```

**Link directo:** http://127.0.0.1:8765

**Thonny:** ejecutar `scripts/arrancar_workbench_thonny.py` (F5).

**Apagar:** Ctrl+C en la terminal del workbench.

---

## 4. Arquitectura UI (Workbench)

### 4.1 Layout

- **Banner superior:** modo, LIVE_BLOCKED, session, aviso chat
- **Escritorio central:** ventanas flotantes (paneles)
- **Barra inferior:** status (mode, live, venue, versión) + botón **QL** (menú)

### 4.2 Abrir paneles

| Método | Cómo |
|--------|------|
| Menú QL | Clic QL → elegir panel |
| Command Palette | **Ctrl+K** → buscar nombre |
| Presets | QL → Research / Trading Paper / Ops |

### 4.3 Paneles principales

| Panel | Función |
|-------|---------|
| **Guided Lab** | Wizard paso a paso (recomendado principiantes) |
| **Chat IA** | Asistente safe-mode (guía, no opera) |
| **Salud / Modo** | Versión, modo tester/paper |
| **Paper Blotter** | Enviar órdenes paper manual |
| **Journal** | Fills paper (incl. mirror binance_demo) |
| **Sesión Paper** | Runner estrategia automática paper |
| **Backtest** | Backtest lab API |
| **Alpha Scanner** | Ranking sintético WB:A/B/C |
| **Market Data** | Snapshot broker |
| **Diagnostics** | Snapshot sistema |
| **Venues** | Registry brokers |
| **API Explorer** | OpenAPI read-only |
| **Reports / Metrics** | Historial backtests sesión |
| **Chat IA** | QL → Chat IA o Ctrl+K → chat |

---

## 5. Guided Lab — flujo completo

**Abrir:** QL → **Guided Lab**

### Sección 0 — Unlock LIVE (opcional)

- Requiere env `QUANTLAB_LIVE_USER` / `QUANTLAB_LIVE_PASSWORD`
- Unlock habilita demo Binance (sim local o testnet)
- **Lock** cierra sesión unlock

### Sección 1 — Venue

| Venue | Qué muestra |
|-------|-------------|
| `binance` | Scan Binance + Demo order |
| `paper` | Solo lab sintético |
| `a3` | Connect A3, MD, instrumentos, snapshot, paper submit |

### Sección 2 — Escanear

- **Scan lab sintético:** universo fake WB (AlphaScanner interno)
- **Scan Binance USDT:** MD público, lista pares + bid/ask (read-only)

### Sección 3–4 — Estrategia + Simular

- Estrategias: `momentum`, `buy_once`
- **Simular backtest:** datos **sintéticos** (no usa símbolos del scan Binance automáticamente en v1.00)

### Sección 5 — Demo order (solo venue binance + unlock)

- MARKET: sin price
- LIMIT: con price
- Mirror: copia fill FILLED al paper journal
- Cancel / Ver abiertas: órdenes LIMIT resting

### Sección A3 (venue a3)

1. md_source: `fake` (CI) o `env` (reMarkets read-only)
2. Estado MD A3
3. Conectar paper A3
4. Listar instrumentos → Snapshot → Enviar paper

### Alpha walk-forward (pipeline Binance)

El pipeline `POST /api/lab/binance/pipeline` usa **walk-forward por defecto** (`walk_forward=True`): ranking en ~70% de las barras y backtest en el 30% restante, **sin overlap**. Así el score no se valida sobre la misma ventana de selección.

- Perfiles / scoring: panel Guided Lab (venue binance) o `GET /api/lab/alpha/profiles`
- Docs: [`docs/scanner/alpha-scanner-guide.md`](scanner/alpha-scanner-guide.md) · estado [`docs/progress/alpha-scanner-optimization-status.md`](progress/alpha-scanner-optimization-status.md)

### Monte Carlo v2

Panel **Monte Carlo** del workbench: shocks sintéticos sobre dataset lab (BuyOnce demo). Payload **schema v2** con `context`, `config`, `metrics`, `relations` y hashes; lecturas legacy v1 se normalizan (“No disponible” si falta campo).

- Parámetros UI: escenarios, barras, ruido bps, seed; API también `scan_id` / `backtest_id` / `store_paths`
- Docs: [`docs/montecarlo/montecarlo-guide.md`](montecarlo/montecarlo-guide.md) · trazabilidad [`docs/montecarlo/montecarlo-traceability.md`](montecarlo/montecarlo-traceability.md) · métodos [`docs/montecarlo/montecarlo-methods.md`](montecarlo/montecarlo-methods.md)

---

## 6. Modos de operación

| Modo | Uso |
|------|-----|
| **tester** | Exploración, sin asumir paper session |
| **paper** / **real** | REAL es alias de PAPER; fills simulados |

Cambiar modo: panel Salud / Modo o API `POST /api/mode`.

---

## 7. Binance — tres niveles

| Nivel | Requiere | Qué hace |
|-------|----------|----------|
| **MD público** | Nada | Scan USDT, bid/ask read-only |
| **Demo sim local** | Unlock LIVE | Fill simulado post-unlock |
| **Testnet** | Unlock + flag + keys | Órdenes a testnet.binance.vision |

**Producción Binance:** bloqueada.

Env demo/testnet:
```
QUANTLAB_LIVE_USER=...
QUANTLAB_LIVE_PASSWORD=...
QUANTLAB_DEMO_USE_TESTNET=1
BINANCE_DEMO_API_KEY=...
BINANCE_DEMO_API_SECRET=...
```

---

## 8. A3 / reMarkets

| Componente | Estado |
|------------|--------|
| MD read-only PyRofex | Opt-in env |
| Fills | PaperBroker |
| Órdenes venue A3 | Bloqueadas (LIVE_BLOCKED) |

Env:
```
QUANTLAB_A3_MD_READONLY=1
QUANTLAB_A3_ENVIRONMENT=simulation
QUANTLAB_A3_USER=...
QUANTLAB_A3_PASSWORD=...
QUANTLAB_A3_ACCOUNT=...
```

CLI preflight:
```bash
uv run quantlab-a3 health
uv run python scripts/a3_md_certify.py --lane sandbox
```

---

## 9. Chat IA — capacidades y límites

**Abrir:** QL → Chat IA · Ctrl+K → `chat`

**Puede:**
- Explicar salud, modo, LIVE_BLOCKED
- Resumen de sesión, reportes, estrategias
- Buscar en docs locales
- Guía de backtest, scanner, venues

**No puede:**
- Enviar órdenes, unlock LIVE, cambiar modo a producción
- Acceder a internet externo (default FakeProvider offline)

**LLM externo (opcional):** configurar `QUANTLAB_LLM_API_KEY` en `.env` (ver `.env.example`).

Preguntas útiles:
- "¿Cómo uso Guided Lab?"
- "¿Qué es LIVE_BLOCKED?"
- "¿Cómo hago backtest?"
- "Explícame Binance demo"

---

## 10. API REST (loopback)

Base: `http://127.0.0.1:8765`

| Ruta | Método | Uso |
|------|--------|-----|
| `/api/health` | GET | Salud |
| `/api/about` | GET | Versión |
| `/api/chat` | POST | Chat `{message}` |
| `/api/lab/backtest` | POST | Backtest sintético |
| `/api/lab/scanner` | POST | Scanner sintético |
| `/api/lab/binance/scan` | POST | Scan MD Binance |
| `/api/lab/binance/scanner` | POST | Ranking alpha klines Binance |
| `/api/lab/binance/pipeline` | POST | Scan alpha + backtest top-N |
| `/api/live/unlock` | POST | Unlock LIVE |
| `/api/live/demo/submit` | POST | Demo order |
| `/api/paper/submit` | POST | Paper order |
| `/api/broker/connect` | POST | Conectar broker |
| `/api/openapi.json` | GET | Catálogo completo |

Explorador: panel **API Explorer**.

---

## 11. Estrategias disponibles (catálogo)

- `dummy`, `buy_once`, `momentum`
- `inventory_mm`, `avellaneda_stoikov` (avanzadas)

Listar: Chat "estrategias" o `GET /api/lab/strategies`.

---

## 12. Flujos operativos recomendados

### Principiante (día 1)

1. Arrancar workbench
2. Guided Lab → venue **paper** → Scan lab → Simular backtest
3. QL → Chat IA → preguntar dudas
4. QL → Diagnostics → ver versión

### Explorar Binance sin operar

1. Guided Lab → venue **binance**
2. Scan Binance USDT
3. Anotar 5 símbolos de la lista

### Demo Binance (con credenciales)

1. Configurar `.env` LIVE + opcional testnet
2. Guided Lab → Unlock → Scan → Demo MARKET
3. Lock al terminar

### A3 reMarkets

1. Configurar `.env` A3
2. `a3_md_certify --lane sandbox`
3. Guided Lab → a3 → env → connect → instrumentos → snapshot → paper

---

## 13. Gaps conocidos (v1.01)

| Feature | Estado |
|---------|--------|
| Scan Binance bid/ask | ✅ |
| Ranking alpha Binance real | ✅ F111 |
| Backtest sintético Guided Lab | ✅ |
| Backtest auto top-5 del scan Binance | ✅ F111 pipeline |
| Chat estilo copilot conversacional | ✅ parcial F111 (FakeProvider + chips; LLM externo opt-in) |

---

## 14. Variables de entorno (.env)

Ver `.env.example`. Nunca commitear `.env`.

---

## 15. Troubleshooting

| Problema | Solución |
|----------|----------|
| :8765 no carga | ¿Terminal workbench abierta? |
| Unlock falla | Verificar QUANTLAB_LIVE_* en env de la misma terminal |
| Error archivo en uso (Thonny) | Workbench ya corre → abrir link directo |
| A3 env no listo | Flag MD + creds + cert sandbox |
| Chat respuestas genéricas | Usar keywords: guided lab, binance, backtest, ayuda |

---

## 16. Documentación adicional en repo

- `docs/ops/LIVE_CREDENTIAL_GATE.md` — unlock y demo
- `docs/FASE_99` … `FASE_110` — Guided Lab arc
- `docs/A3_RUNBOOK.md` — A3 CLI
- `docs/scanner/` — Alpha Scanner + walk-forward
- `docs/montecarlo/` — Monte Carlo v2 (guía, métodos, trazabilidad)
- `RESUMEN_PROYECTO.txt` — estado operativo
- `RETOMAR.txt` — checkpoint desarrollo

---

## 17. Instrucciones para la IA que recibe este documento

Cuando el usuario pregunte cómo operar:

1. Identificar objetivo: aprender / binance MD / demo / A3 / backtest
2. Verificar prerequisitos (workbench corriendo, .env si aplica)
3. Dar pasos numerados en Guided Lab o panel específico
4. Recordar LIVE_BLOCKED y que REAL=PAPER
5. No pedir secrets en chat; indicar variables .env
6. Si pide "5 monedas + estrategia": en v1.00 guiar manual; post-F111 usar pipeline Binance

---

*Fin guía — QuantLab Workbench · Rosario granos / quant research*
