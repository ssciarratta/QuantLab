# Fase 6 — Backtester bar-based (5A)

**Numeración:** oficial alineada (`docs/ROADMAP_ALIGNED.md`)  
**Objetivo:** Validar arquitectura de simulación con OHLCV ≥ 1m.

| Módulo | Contenido | Estado |
|--------|-----------|--------|
| 1 | Facade `BarBacktester` + políticas baseline | ✅ |
| 2 | Contabilidad cuadrada (`assert_accounting_balanced`) | ✅ |
| 3 | Golden runs reproducibles + `SimpleMomentumStrategy` | ✅ |

**Estado de fase:** ver certificado `docs/audit/FASE_06_APPROVED.md`

## API

```python
from quantlab.backtester import BarBacktester, BarBacktestConfig
from quantlab.research.strategies import BuyOnceStrategy

bt = BarBacktester(BarBacktestConfig(experiment_id="demo", initial_cash=Decimal("10000")))
result = bt.run(BuyOnceStrategy({"quantity": "1"}), bars)
# result.simulation / result.metrics / result.accounting
```

## Invariantes 5A

- Un solo `instrument_id` por corrida
- Duración de barra ≥ `min_timeframe_minutes` (default 1)
- Timestamps estrictamente ascendentes
- Contabilidad: cash reconstruido ≈ cash reportado; equity = cash + marks
- Golden fingerprint **sin** IDs aleatorios ni `computed_at`

## No alcance (Fase 7 / 5B)

- Market making / inventory skew
- Partial fill / cancel / replace
- Latency wall-clock / book-based slippage
