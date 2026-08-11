"""MC ligado al Sim: horizonte, ruido estrés y overlay leverage como Comparar."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from quantlab.core.types.results import EquityPoint
from quantlab.montecarlo.limits import (
    MAX_BARS,
    SIM_LINKED_DEFAULT_NOISE_BPS,
)
from quantlab.workbench import lab_services
from quantlab.workbench.lab_services import _mc_sim_with_compare_overlay


def test_max_bars_allows_compare_horizon() -> None:
    assert MAX_BARS >= 2000
    assert SIM_LINKED_DEFAULT_NOISE_BPS >= 50.0


def test_overlay_scales_pnl_like_compare() -> None:
    from datetime import UTC, datetime, timedelta

    start = datetime(2026, 1, 1, tzinfo=UTC)
    curve = (
        EquityPoint(timestamp=start, equity=Decimal("100")),
        EquityPoint(
            timestamp=start + timedelta(hours=1), equity=Decimal("110")
        ),
    )
    sim = SimpleNamespace(equity_curve=curve, fills=())
    out = _mc_sim_with_compare_overlay(
        sim,  # type: ignore[arg-type]
        initial_cash=Decimal("100"),
        leverage=Decimal("10"),
        simulate_liquidation=False,
        apply_funding=False,
        funding_rates=None,
    )
    # PnL 1x = +10 → ×10 = +100 → final 200
    assert out.equity_curve[-1].equity == Decimal("200")


def test_resolve_bumps_horizon_to_period(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import UTC, datetime, timedelta

    from quantlab.core.types.market import Bar

    bars: list[Bar] = []
    px = Decimal("100")
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    for i in range(2500):
        ts = t0 + timedelta(hours=i)
        bars.append(
            Bar(
                instrument_id="BNF:APTUSDT",
                timestamp_open=ts,
                timestamp_close=ts + timedelta(hours=1),
                open=px,
                high=px + Decimal("1"),
                low=px - Decimal("1"),
                close=px,
                volume=Decimal("10"),
                timeframe="1h",
            )
        )
    resolved = MagicMock()
    resolved.instrument_id = "BNF:APTUSDT"
    resolved.underlying = "APT"

    monkeypatch.setattr(
        "quantlab.brokers.md_router.fetch_bars_for_instrument",
        lambda *a, **k: (resolved, bars),
    )

    linked = lab_services._resolve_mc_from_sim_context(
        {
            "pairs": [{"venue": "binance", "underlying": "APT"}],
            "market_type": "futures",
            "interval": "1h",
            "period_days": 90,
            "strategy_id": "momentum",
            "capital_mode": "fixed",
            "initial_capital": "100",
            "per_trade_usd": "2",
            "leverage": "10",
            "liq": True,
            "funding": True,
        },
        n_bars=60,  # form corto → debe subir al período
        strategy_id_fallback="momentum",
    )
    assert linked["n_bars_effective"] >= 2000
    assert linked["leverage"] == Decimal("10")
    assert linked["simulate_liquidation"] is True
    assert linked["apply_funding"] is True
    assert linked["horizon_warning"]


def test_mc_sim_context_ux_limits() -> None:
    from pathlib import Path

    static = Path(__file__).resolve().parents[3] / "src/quantlab/workbench/static"
    mc = (static / "js/panes/montecarlo.js").read_text(encoding="utf-8")
    assert "MC_MAX_BARS = 5000" in mc
    assert "SIM_LINKED_NOISE = 50" in mc
    assert 'max="5000"' in mc
    sim = (static / "js/panes/simulator.js").read_text(encoding="utf-8")
    assert "noise_bps: 50" in sim
    assert "MC_MAX_BARS = 5000" in sim
