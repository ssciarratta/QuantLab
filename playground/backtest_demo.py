#!/usr/bin/env python3
"""Demo backtest QuantLab — SOLO PAPER / simulación (playground).

Uso (desde la raíz del repo):
  uv run python playground/backtest_demo.py
"""

from __future__ import annotations

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.lab_services import run_lab_backtest


def main() -> None:
    assert LIVE_BLOCKED is True, "LIVE debe permanecer bloqueado"
    print(f"QuantLab {__version__} · LIVE_BLOCKED={LIVE_BLOCKED}")

    result = run_lab_backtest(
        strategy_id="momentum",
        n_bars=24,
        experiment_id="playground-backtest-1",
    )
    print("ok:", result.get("ok"))
    print("strategy:", result.get("strategy_id"))
    print("fills:", result.get("n_fills"))
    print("final_equity:", result.get("final_equity"))
    print("live_routing:", result.get("live_routing"))
    print("live_blocked:", result.get("live_blocked"))
    metrics = result.get("metrics") or {}
    for key in ("sharpe", "max_drawdown", "win_rate", "profit_factor"):
        if key in metrics:
            print(f"  {key}: {metrics[key]}")


if __name__ == "__main__":
    main()
