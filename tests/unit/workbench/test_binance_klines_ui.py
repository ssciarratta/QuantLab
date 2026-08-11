"""Klines UI — recorte a vela en formación (PAPER / testnet gráfico SLT)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.workbench.api import (
    WorkbenchState,
    _clip_kline_bars_for_ui,
    _forming_kline_open,
    handle_post_binance_klines,
)


def test_forming_kline_open_aligns_to_interval() -> None:
    now = 1_786_471_597
    assert _forming_kline_open(now, "1m") == 1_786_471_560
    assert _forming_kline_open(now, "5m") == 1_786_471_500


def test_clip_kline_bars_drops_future_candles() -> None:
    now = 1_000_000
    forming = _forming_kline_open(now, "1m")
    bars = [
        {"time": forming - 120, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0},
        {"time": forming, "open": 2.0, "high": 2.0, "low": 2.0, "close": 2.0},
        {"time": forming + 60, "open": 3.0, "high": 3.0, "low": 3.0, "close": 3.0},
    ]
    out = _clip_kline_bars_for_ui(bars, interval="1m", now_sec=now)
    assert [b["time"] for b in out] == [forming - 120, forming]


def test_handle_post_binance_klines_includes_server_now(monkeypatch) -> None:
    now = datetime.now(tz=UTC)
    t0 = now - timedelta(minutes=2)
    t1 = now - timedelta(minutes=1)
    t2 = now + timedelta(minutes=1)

    class _FakeClient:
        def klines(self, symbol: str, *, interval: str = "1h", limit: int = 24) -> list[Bar]:
            _ = symbol, interval, limit

            def _bar(t: datetime, px: str) -> Bar:
                return Bar(
                    instrument_id="BN:BTCUSDT",
                    open=Decimal(px),
                    high=Decimal(px),
                    low=Decimal(px),
                    close=Decimal(px),
                    volume=Decimal("1"),
                    timestamp_open=t,
                    timestamp_close=t,
                    timeframe="1m",
                )

            return [_bar(t0, "1"), _bar(t1, "2"), _bar(t2, "3")]

    monkeypatch.setattr(
        "quantlab.brokers.binance.public_md.BinancePublicMdClient",
        _FakeClient,
    )

    out = handle_post_binance_klines(
        WorkbenchState(),
        {
            "symbol": "BTCUSDT",
            "interval": "1m",
            "limit": 10,
            "market_type": "spot",
            "network": "mainnet",
        },
    )
    assert isinstance(out["server_now"], int)
    forming = _forming_kline_open(out["server_now"], "1m")
    times = [b["time"] for b in out["bars"]]
    assert all(t <= forming for t in times)
    assert int(t2.timestamp()) not in times
