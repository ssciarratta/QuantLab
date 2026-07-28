"""Venue lab scanner — path curado con MD mockeado (sin red)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.research.sim.symbol_map import ResolvedInstrument
from quantlab.workbench import lab_services


def _bars(sym: str, n: int = 12) -> list[Bar]:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    out: list[Bar] = []
    for i in range(n):
        px = Decimal(100 + (i % 5))
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"BNF:{sym}",
                open=px,
                high=px + Decimal("1"),
                low=px - Decimal("1"),
                close=px,
                volume=Decimal(str(1000 + i * 10)),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


def test_venue_scanner_curated_binance_futures_mock() -> None:
    coins = ["BTC", "ETH", "SOL", "BNB", "XRP"]

    def fake_fetch(
        underlying: str,
        *,
        venue: str,
        market_type: str,
        interval: str = "1h",
        kline_limit: int = 24,
    ) -> tuple[ResolvedInstrument, list[Bar]]:
        del interval, kline_limit
        sym = f"{underlying}USDT"
        resolved = ResolvedInstrument(
            venue=venue,
            market_type=market_type,
            underlying=underlying,
            symbol=sym,
            instrument_id=f"BNF:{sym}",
        )
        return resolved, _bars(sym)

    with patch(
        "quantlab.brokers.md_router.fetch_bars_for_instrument",
        side_effect=fake_fetch,
    ):
        out = lab_services.run_venue_lab_scanner(
            venue="binance",
            market_type="futures",
            top_n=3,
            symbol_limit=5,
            underlyings=coins,
            kline_limit=12,
        )
    assert out["ok"] is True
    assert out["kind"] == "venue_scanner"
    assert out["venue"] == "binance"
    assert out["market_type"] == "futures"
    assert len(out["scores"]) >= 1
    assert "recommendation" in out["scores"][0]
    assert out["scores"][0].get("underlying")
    assert "recommendations" in out


def test_venue_scanner_hl_spot_rejected() -> None:
    with pytest.raises(ValidationError, match="futures"):
        lab_services.run_venue_lab_scanner(
            venue="hyperliquid",
            market_type="spot",
            top_n=3,
            symbol_limit=5,
        )
