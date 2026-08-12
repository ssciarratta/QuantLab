"""Tests API pairwise scanner (mock Binance)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

from quantlab.core.types.market import Bar
from quantlab.workbench import lab_services


def _fake_bars(sym: str, n: int = 150, *, drift: int = 1) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + drift * i)
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"BN:{sym}",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal("1000") + Decimal(i * 10),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


@pytest.fixture
def binance_universe_pw() -> dict[str, list[Bar]]:
    return {
        "BTCUSDT": _fake_bars("BTCUSDT", drift=2),
        "ETHUSDT": _fake_bars("ETHUSDT", drift=3),
        "BNBUSDT": _fake_bars("BNBUSDT", drift=1),
        "SOLUSDT": _fake_bars("SOLUSDT", drift=4),
    }


def test_pairwise_lab_scanner_returns_signals(binance_universe_pw: dict[str, list[Bar]]) -> None:
    symbols = list(binance_universe_pw.keys())
    with (
        patch(
            "quantlab.brokers.binance.public_md.BinancePublicMdClient.list_spot_symbols",
            return_value=symbols,
        ),
        patch(
            "quantlab.brokers.binance.public_md.fetch_universe_bars",
            return_value=binance_universe_pw,
        ),
    ):
        out = lab_services.run_pairwise_lab_scanner(
            symbol_limit=4,
            kline_limit=150,
            detectors=("contemporary_correlation",),
            top_n=5,
            include_signals=True,
        )
    assert out["ok"] is True
    assert out["kind"] == "pairwise_scanner"
    assert out["market_type"] == "spot"
    assert out["n_symbols"] >= 2
    assert "signals" in out
    if out["signals"]:
        assert "recommended_strategy" in out["signals"][0]


def test_pairwise_futures_scanner(binance_universe_pw: dict[str, list[Bar]]) -> None:
    symbols = list(binance_universe_pw.keys())
    fut_bars: dict[str, list[Bar]] = {}
    for sym, bars in binance_universe_pw.items():
        fut_bars[sym] = [
            Bar(
                instrument_id=f"BNF:{sym}",
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                timestamp_open=b.timestamp_open,
                timestamp_close=b.timestamp_close,
                timeframe=b.timeframe,
            )
            for b in bars
        ]
    with (
        patch(
            "quantlab.brokers.binance.futures_public_md.BinanceFuturesPublicMdClient.list_futures_symbols",
            return_value=symbols,
        ),
        patch(
            "quantlab.brokers.binance.futures_public_md.fetch_futures_bars",
            return_value=fut_bars,
        ),
    ):
        out = lab_services.run_pairwise_lab_scanner(
            market_type="futures",
            symbol_limit=4,
            kline_limit=150,
            detectors=("contemporary_correlation",),
            top_n=5,
            include_signals=True,
        )
    assert out["ok"] is True
    assert out["market_type"] == "futures"
    assert out["venue"] == "binance"


def test_pairwise_kline_limit_min() -> None:
    with pytest.raises(Exception) as exc:
        lab_services.run_pairwise_lab_scanner(kline_limit=50)
    assert "120" in str(exc.value)


def test_get_lab_detectors_lists_pairwise() -> None:
    from quantlab.workbench.api import WorkbenchState, handle_get_lab_detectors

    out = handle_get_lab_detectors(WorkbenchState())
    assert out["ok"] is True
    ids = {d["detector_id"] for d in out["detectors"]}
    assert "lagged_correlation" in ids
    assert "cointegration" in ids
