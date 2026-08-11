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


def test_venue_scanner_a3_futures_mock() -> None:
    coins = ["SOJ/MAY26", "MAI/JUL26", "TRI/DIC25", "DLR/DIC25"]

    def fake_fetch(
        underlying: str,
        *,
        venue: str,
        market_type: str,
        interval: str = "1h",
        kline_limit: int = 24,
    ) -> tuple[ResolvedInstrument, list[Bar]]:
        del interval, kline_limit
        assert venue == "a3"
        assert market_type == "futures"
        resolved = ResolvedInstrument(
            venue="a3",
            market_type="futures",
            underlying=underlying,
            symbol=underlying,
            instrument_id=f"A3:{underlying}",
        )
        return resolved, _bars(underlying.replace("/", ""))

    with patch(
        "quantlab.brokers.md_router.fetch_bars_for_instrument",
        side_effect=fake_fetch,
    ):
        out = lab_services.run_venue_lab_scanner(
            venue="a3",
            market_type="futures",
            top_n=3,
            symbol_limit=8,
            underlyings=coins,
            kline_limit=12,
            profile="trend",
        )
    assert out["ok"] is True
    assert out["venue"] == "a3"
    assert out["market_type"] == "futures"
    assert len(out["scores"]) >= 1


def test_venue_scanner_a3_spot_rejected() -> None:
    with pytest.raises(ValidationError, match="futures"):
        lab_services.run_venue_lab_scanner(
            venue="a3",
            market_type="spot",
            top_n=3,
            symbol_limit=5,
        )


def test_symbol_limit_batches_allowed() -> None:
    assert lab_services.SCANNER_SYMBOL_BATCHES == (20, 30, 40, 50)
    lab_services._validate_symbol_limit(1)
    lab_services._validate_symbol_limit(50)
    lab_services._validate_symbol_limit(500)
    lab_services._validate_symbol_limit(lab_services.SYMBOL_LIMIT_ALL)
    with pytest.raises(ValidationError, match="symbol_limit"):
        lab_services._validate_symbol_limit(501)
    with pytest.raises(ValidationError, match="symbol_limit"):
        lab_services._validate_symbol_limit(-1)


def test_top_n_free_range() -> None:
    lab_services._validate_top_n(1)
    lab_services._validate_top_n(100)
    with pytest.raises(ValidationError, match="top_n"):
        lab_services._validate_top_n(0)
    with pytest.raises(ValidationError, match="top_n"):
        lab_services._validate_top_n(101)


def test_symbol_limit_all_uses_full_curated_universe() -> None:
    coins = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "LINK"]

    def fake_fetch(
        underlying: str,
        *,
        venue: str,
        market_type: str,
        interval: str = "1h",
        kline_limit: int = 24,
    ) -> tuple[ResolvedInstrument, list[Bar]]:
        del interval, kline_limit, venue, market_type
        sym = f"{underlying}USDT"
        resolved = ResolvedInstrument(
            venue="binance",
            market_type="futures",
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
            symbol_limit=0,
            underlyings=coins,
            kline_limit=12,
            profile="trend",
        )
    assert out["universe_mode"] == "custom"
    assert out["n_universe"] == len(coins)
    assert out["symbol_limit"] == 0
    assert out.get("requested_underlyings") == coins


def test_multi_venue_scanner_comparison_mock() -> None:
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
        # Sesgo leve por venue para que la comparación tenga delta
        bump = {"binance": 0, "okx": 2, "bybit": 1}.get(venue, 0)
        sym = f"{underlying}USDT"
        prefix = {"binance": "BNF", "okx": "OKX", "bybit": "BYB"}.get(venue, "BNF")
        resolved = ResolvedInstrument(
            venue=venue,
            market_type=market_type,
            underlying=underlying,
            symbol=sym,
            instrument_id=f"{prefix}:{sym}",
        )
        bars = _bars(sym)
        # alterar close un poco por venue
        if bump and bars:
            last = bars[-1]
            bars[-1] = Bar(
                instrument_id=last.instrument_id,
                open=last.open,
                high=last.high + Decimal(bump),
                low=last.low,
                close=last.close + Decimal(bump),
                volume=last.volume,
                timestamp_open=last.timestamp_open,
                timestamp_close=last.timestamp_close,
                timeframe=last.timeframe,
            )
        return resolved, bars

    with patch(
        "quantlab.brokers.md_router.fetch_bars_for_instrument",
        side_effect=fake_fetch,
    ):
        out = lab_services.run_multi_venue_lab_scanner(
            venues=["binance", "okx"],
            market_type="futures",
            top_n=3,
            symbol_limit=5,
            underlyings=coins,
            kline_limit=12,
            profile="trend",
        )
    assert out["ok"] is True
    assert out["kind"] == "multi_venue_scanner"
    assert len(out["by_venue"]) == 2
    assert out["by_venue"][0]["venue"] == "binance"
    assert out["by_venue"][1]["venue"] == "okx"
    assert "comparison" in out
    assert out["comparison"]["venue_summary"]
    assert out["scores"]  # compat primer venue


def test_venue_scanner_accepts_single_underlying() -> None:
    def fake_fetch(
        underlying: str,
        *,
        venue: str,
        market_type: str,
        interval: str = "1h",
        kline_limit: int = 24,
    ) -> tuple[ResolvedInstrument, list[Bar]]:
        del interval, kline_limit
        assert venue == "binance"
        assert market_type == "futures"
        sym = f"{underlying}USDT"
        # Volúmenes distintos para que el min-max anclado discrimine.
        n = 12
        base = datetime(2024, 1, 1, tzinfo=UTC)
        vol = Decimal("5000") if underlying == "NEAR" else Decimal("1000")
        bars: list[Bar] = []
        for i in range(n):
            px = Decimal(100 + (i % 5) + (10 if underlying == "NEAR" else 0))
            t0 = base + timedelta(hours=i)
            bars.append(
                Bar(
                    instrument_id=f"BNF:{sym}",
                    open=px,
                    high=px + Decimal("1"),
                    low=px - Decimal("1"),
                    close=px,
                    volume=vol + Decimal(i),
                    timestamp_open=t0,
                    timestamp_close=t0 + timedelta(hours=1),
                    timeframe="1h",
                )
            )
        resolved = ResolvedInstrument(
            venue=venue,
            market_type=market_type,
            underlying=underlying,
            symbol=sym,
            instrument_id=f"BNF:{sym}",
        )
        return resolved, bars

    with patch(
        "quantlab.brokers.md_router.fetch_bars_for_instrument",
        side_effect=fake_fetch,
    ):
        out = lab_services.run_venue_lab_scanner(
            venue="binance",
            market_type="futures",
            top_n=1,
            symbol_limit=0,
            underlyings=["NEAR"],
            kline_limit=12,
            profile="trend",
        )
    assert out["ok"] is True
    assert out.get("score_mode") == "anchored_cross_section"
    assert out.get("score_anchors")
    assert out.get("universe_mode") == "puntual"
    assert out.get("requested_underlyings") == ["NEAR"]
    assert len(out["scores"]) == 1
    assert out["scores"][0].get("underlying") == "NEAR"
    comp = float(out["scores"][0].get("composite") or 0)
    assert comp > 0.0


def test_venue_scanner_rejects_empty_underlyings() -> None:
    with pytest.raises(ValidationError, match="underlyings vacío"):
        lab_services.run_venue_lab_scanner(
            venue="binance",
            market_type="futures",
            underlyings=[],
            kline_limit=12,
        )


def test_venue_scanner_missing_requested_coin_clear_error() -> None:
    def fake_fetch(
        underlying: str,
        *,
        venue: str,
        market_type: str,
        interval: str,
        kline_limit: int,
    ) -> tuple[ResolvedInstrument, list[Bar]]:
        raise ValidationError(f"símbolo inexistente: {underlying}")

    with patch(
        "quantlab.brokers.md_router.fetch_bars_for_instrument",
        side_effect=fake_fetch,
    ):
        with pytest.raises(ValidationError, match="no se encontró"):
            lab_services.run_venue_lab_scanner(
                venue="binance",
                market_type="futures",
                underlyings=["ZZZNOPE"],
                kline_limit=12,
                profile="trend",
            )
