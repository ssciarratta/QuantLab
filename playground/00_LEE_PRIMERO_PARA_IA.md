# QuantLab — Pack para IA externa (Claude / Gemini) — SOLO BACKTESTS

**Versión tip del pack:** 0.90.0  
**Repo real (PC del dueño):** `C:\Users\ssciarratta\Desktop\QuantLab`  
**Fecha pack:** 2026-07-26

---

## 1. Qué es QuantLab (léelo primero)

QuantLab es un **laboratorio cuantitativo**, NO un bot de trading live suelto.

- Modos: TESTER / PAPER / REAL  
- **REAL = alias de PAPER** (MD/cuenta pueden ser “reales”; fills simulados)  
- **LIVE routing está BLOQUEADO** (`LIVE_BLOCKED = True`)  
- Stack: Python + Workbench HTML/JS vanilla (sin React)  
- Objetivo de producto del dueño (largo plazo):  
  1) Pantalla amigable: elegir venue (Binance luego A3)  
  2) Escanear activos  
  3) Elegir estrategia  
  4) Simular / paper  
  5) Recién después, LIVE gated (Binance primero, luego A3)

**Tu rol (IA externa):** ayudar a **experimentar backtests / scanner / estrategias en paper**.  
**NO tu rol:** flip LIVE, order routing venue, reescribir Workbench, inventar certificados `FASE_*_APPROVED.md`.

---

## 2. Reglas irrenunciables (si las rompés, el pack se descarta)

1. `LIVE_BLOCKED` debe permanecer `True`. No lo cambies.  
2. Prohibido: `place_order` venue, `set_live`, flip live, submit live.  
3. Prohibido crear `docs/audit/FASE_*_APPROVED.md`.  
4. No reescribas `workbench/server.py`, paper journal/book, ni `execution/live_gate.py`.  
5. Cambios solo en `playground/` o scripts de experimento.  
6. Respuestas en español si el usuario habla español.  
7. Si no estás seguro: preguntá; no inventes APIs.

---

## 3. Cómo correr (en la PC del dueño)

```bash
cd "C:\Users\ssciarratta\Desktop\QuantLab"
uv sync
uv run python -c "from quantlab import __version__; from quantlab.execution.live_gate import LIVE_BLOCKED; print(__version__, LIVE_BLOCKED)"
# Esperado: 0.90.x True
```

Demos del pack (también están en el repo bajo `playground/`):

```bash
uv run python playground/backtest_demo.py
uv run python playground/scan_demo.py
uv run pytest tests/unit/backtester/test_bar_backtester.py -q
```

Workbench UI (opcional):

```bash
uv run quantlab-workbench
# http://127.0.0.1:8765
```

---

## 4. APIs útiles para backs (ya existen)

```python
from quantlab.workbench.lab_services import run_lab_backtest, run_lab_scanner

run_lab_scanner(top_n=3)
run_lab_backtest(strategy_id="momentum", n_bars=24)
```

Backtester de barras:

```python
from quantlab.backtester import BarBacktester, BarBacktestConfig
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy
from quantlab.research.strategies.buy_once import BuyOnceStrategy
```

Estrategias típicas: `momentum`, `buy_once` (vía lab / catalog).

---

## 5. Archivos incluidos en este ZIP

| Path | Para qué |
|------|----------|
| `00_LEE_PRIMERO_PARA_IA.md` | Este briefing |
| `RESUMEN_PROYECTO.txt` | Estado operativo del proyecto |
| `PROJECT_MEMORY.md` | Memoria tip (invariantes) |
| `playground/backtest_demo.py` | Demo backtest |
| `playground/scan_demo.py` | Demo scanner |
| `tests/unit/backtester/test_bar_backtester.py` | Tests de referencia |
| `src/quantlab/backtester/` | Motor backtest barras |
| `src/quantlab/simulation/` | Simulación de barras |
| `src/quantlab/research/` | Estrategias / alpha scanner |
| `src/quantlab/metrics/` | Métricas |
| `src/quantlab/execution/live_gate.py` | Gate LIVE (NO tocar) |
| `pyproject.toml` | Dependencias / scripts |

**Nota:** este ZIP es un **contexto + demos**. Para imports completos del Workbench, el dueño corre comandos en el repo completo. No asumas que el ZIP solo es un producto instalable mínimo sin el resto del monorepo.

---

## 6. Prompt sugerido al abrir el chat con este ZIP

> Leé `00_LEE_PRIMERO_PARA_IA.md` y `RESUMEN_PROYECTO.txt`.  
> Ayudame a experimentar backtests en QuantLab (paper only).  
> Respetá LIVE_BLOCKED=True. No toques live routing.  
> Empezá mejorando o extendiendo `playground/backtest_demo.py`.

---

## 7. Qué NO pedir a esta IA externa

- “Activá live en Binance”  
- “Sacá LIVE_BLOCKED”  
- “Generá certificado FASE_XX_APPROVED”  
- “Reescribí el Workbench en React”

Eso lo hace el agente profesional del repo Cursor, con gates de seguridad.
