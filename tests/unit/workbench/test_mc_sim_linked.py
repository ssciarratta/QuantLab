"""MC ligado al Simulador: usa moneda/estrategia de sim_context (no WB:SYN)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

import pytest

from quantlab.core.types.market import Bar
from quantlab.workbench import lab_services


def _fake_bars(n: int = 40, instrument_id: str = "BN:BTCUSDT") -> list[Bar]:
    from datetime import UTC, datetime, timedelta

    start = datetime(2026, 1, 1, tzinfo=UTC)
    out: list[Bar] = []
    px = Decimal("100")
    for i in range(n):
        ts = start + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=instrument_id,
                timestamp_open=ts,
                timestamp_close=ts + timedelta(hours=1),
                open=px,
                high=px + Decimal("1"),
                low=px - Decimal("1"),
                close=px + Decimal("0.5"),
                volume=Decimal("10"),
                timeframe="1h",
            )
        )
        px = px + Decimal("0.25")
    return out


def test_mc_sim_context_uses_real_symbol_and_strategy(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    bars = _fake_bars(48, "BN:BTCUSDT")
    resolved = MagicMock()
    resolved.instrument_id = "BN:BTCUSDT"
    resolved.underlying = "BTC"

    def _fake_fetch(
        underlying: str,
        *,
        venue: str,
        market_type: str,
        interval: str,
        kline_limit: int,
    ) -> tuple[Any, list[Bar]]:
        assert underlying in {"BTC", "BTCUSDT"}
        assert venue == "binance"
        return resolved, bars

    monkeypatch.setattr(
        "quantlab.brokers.md_router.fetch_bars_for_instrument",
        _fake_fetch,
    )

    sim_context = {
        "source": "simulator",
        "kind": "compare",
        "strategy_id": "momentum",
        "strategy_label": "Momentum",
        "coin": "BTC",
        "coins": ["BTC"],
        "venues": ["binance"],
        "pairs": [{"venue": "binance", "underlying": "BTC", "ticker": "BTCUSDT"}],
        "market_type": "futures",
        "interval": "1h",
        "period_days": 7,
        "leverage": 3,
        "capital_mode": "fixed",
        "initial_capital": "25000",
        "per_trade_usd": "1000",
        "summary_line": "Comparar · BTC · binance · Momentum · 1h · 7d · x3",
    }

    out = lab_services.run_lab_montecarlo(
        n_scenarios=4,
        n_bars=20,
        seed=7,
        persist=False,
        sim_context=sim_context,
        montecarlo_root=tmp_path,
    )

    assert out["ok"] is True
    assert out["mode"] == "sim_linked"
    assert out["context"]["sim_linked"] is True
    assert out["context"]["strategy_id"] == "momentum" or out["context"].get(
        "strategy_name"
    ) in {"momentum", "Momentum"}
    assert out["dataset"]["synthetic"] is False
    assert "BTC" in str(out["dataset"]["symbol"]) or "BTC" in str(
        out["dataset"]["dataset_id"]
    )
    assert float(out["initial_equity"]) == 25000.0
    assert out["context"].get("sim_context") is not None
    assert "orphan_warning" not in out["context"]


def test_mc_without_sim_context_stays_synthetic(tmp_path: Any) -> None:
    out = lab_services.run_lab_montecarlo(
        n_scenarios=3,
        n_bars=16,
        seed=1,
        persist=False,
        montecarlo_root=tmp_path,
    )
    assert out["mode"] == "technical_lab"
    assert out["dataset"]["synthetic"] is True
    assert out["context"].get("sim_linked") is not True
