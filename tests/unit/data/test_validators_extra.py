"""Cobertura extra: validators de calidad (paths no cubiertos por test_quality_ohlcv)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from quantlab.core.types.enums import OrderSide
from quantlab.core.types.market import Bar, Trade
from quantlab.data.quality.validators import (
    QualityIssue,
    QualityReport,
    QualitySeverity,
    sanitize_bars,
    validate_bars,
    validate_trades,
)


def _ts(minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=minute)


def _bar(
    *,
    minute: int = 0,
    instrument_id: str = "X",
    open_: str = "10",
    high: str = "11",
    low: str = "9",
    close: str = "10.5",
    volume: str = "1",
) -> Bar:
    t0 = _ts(minute)
    return Bar(
        instrument_id=instrument_id,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


def _trade(
    *,
    minute: int = 0,
    instrument_id: str = "X",
    trade_id: str = "t1",
    price: str = "10",
    quantity: str = "1",
) -> Trade:
    return Trade(
        instrument_id=instrument_id,
        price=Decimal(price),
        quantity=Decimal(quantity),
        side=OrderSide.BUY,
        timestamp=_ts(minute),
        trade_id=trade_id,
    )


def _raw_bar(**fields: Any) -> Bar:
    """Bar sin __post_init__ (permite OHLC/ts inválidos para ejercer el validador)."""
    bar = object.__new__(Bar)
    t0 = _ts(0)
    defaults: dict[str, Any] = {
        "instrument_id": "X",
        "open": Decimal("10"),
        "high": Decimal("11"),
        "low": Decimal("9"),
        "close": Decimal("10"),
        "volume": Decimal("1"),
        "timestamp_open": t0,
        "timestamp_close": t0 + timedelta(minutes=1),
        "timeframe": "1m",
    }
    defaults.update(fields)
    for key, value in defaults.items():
        object.__setattr__(bar, key, value)
    return bar


def _raw_trade(**fields: Any) -> Trade:
    trade = object.__new__(Trade)
    defaults: dict[str, Any] = {
        "instrument_id": "X",
        "price": Decimal("10"),
        "quantity": Decimal("1"),
        "side": OrderSide.BUY,
        "timestamp": _ts(0),
        "trade_id": "t1",
    }
    defaults.update(fields)
    for key, value in defaults.items():
        object.__setattr__(trade, key, value)
    return trade


# --- QualityReport ---


def test_quality_report_flags() -> None:
    empty = QualityReport(())
    assert not empty.has_fatal and not empty.has_error
    fatal = QualityReport(
        (QualityIssue("naive_timestamp", QualitySeverity.FATAL, "x"),)
    )
    assert fatal.has_fatal
    err = QualityReport(
        (QualityIssue("non_positive_price", QualitySeverity.ERROR, "x"),)
    )
    assert err.has_error and not err.has_fatal


# --- validate_trades ---


def test_validate_trades_naive_timestamp() -> None:
    report = validate_trades([_raw_trade(timestamp=datetime(2024, 1, 1))])
    assert any(i.code == "naive_timestamp" for i in report.issues)
    assert report.has_fatal


def test_validate_trades_non_positive_price_and_qty() -> None:
    bad_px = _raw_trade(price=Decimal("0"), trade_id="t2", timestamp=_ts(0))
    bad_qty = _raw_trade(quantity=Decimal("-1"), trade_id="t3", timestamp=_ts(1))
    report = validate_trades([bad_px, bad_qty])
    codes = {i.code for i in report.issues}
    assert "non_positive_price" in codes
    assert "non_positive_qty" in codes
    assert report.has_error


def test_validate_trades_out_of_order_and_duplicates() -> None:
    t0 = _trade(minute=0, trade_id="a")
    t1 = _trade(minute=2, trade_id="b")
    t_ooo = _trade(minute=1, trade_id="c")  # atrás respecto de t1
    t_dup_ts = _trade(minute=2, trade_id="d")  # mismo ts que t1
    t_dup_id = _trade(minute=3, trade_id="a")  # trade_id duplicado
    report = validate_trades([t0, t1, t_ooo, t_dup_ts, t_dup_id])
    codes = [i.code for i in report.issues]
    assert "out_of_order" in codes
    assert "duplicate_timestamp" in codes
    assert "duplicate" in codes
    assert any(i.severity is QualitySeverity.WARNING for i in report.issues)


def test_validate_trades_multi_instrument_independent_order() -> None:
    a0 = _trade(minute=0, instrument_id="A", trade_id="a0")
    b0 = _trade(minute=5, instrument_id="B", trade_id="b0")
    a1 = _trade(minute=1, instrument_id="A", trade_id="a1")
    report = validate_trades([a0, b0, a1])
    assert not any(i.code == "out_of_order" for i in report.issues)


# --- validate_bars ---


def test_validate_bars_empty_volume_info() -> None:
    report = validate_bars([_bar(volume="0")])
    assert any(i.code == "empty_bar" and i.severity is QualitySeverity.INFO for i in report.issues)
    assert not report.has_error


def test_validate_bars_naive_timestamp() -> None:
    naive = _raw_bar(
        timestamp_open=datetime(2024, 1, 1),
        timestamp_close=datetime(2024, 1, 1, 0, 1),
    )
    report = validate_bars([naive])
    assert any(i.code == "naive_bar_ts" for i in report.issues)
    assert report.has_fatal


def test_validate_bars_ohlc_and_negative_volume() -> None:
    # high < max(open, close)
    bad_high = _raw_bar(
        open=Decimal("10"),
        high=Decimal("9"),
        low=Decimal("8"),
        close=Decimal("10"),
        timestamp_open=_ts(0),
        timestamp_close=_ts(1),
    )
    # low > min(open, close)
    bad_low = _raw_bar(
        open=Decimal("10"),
        high=Decimal("12"),
        low=Decimal("11"),
        close=Decimal("10"),
        timestamp_open=_ts(2),
        timestamp_close=_ts(3),
    )
    # high < low
    bad_range = _raw_bar(
        open=Decimal("10"),
        high=Decimal("8"),
        low=Decimal("12"),
        close=Decimal("10"),
        timestamp_open=_ts(4),
        timestamp_close=_ts(5),
    )
    neg_vol = _raw_bar(
        volume=Decimal("-1"),
        timestamp_open=_ts(6),
        timestamp_close=_ts(7),
    )
    report = validate_bars([bad_high, bad_low, bad_range, neg_vol])
    codes = {i.code for i in report.issues}
    assert "ohlc_high" in codes
    assert "ohlc_low" in codes
    assert "ohlc_range" in codes
    assert "negative_volume" in codes
    assert report.has_error


def test_validate_bars_duplicate_and_out_of_order() -> None:
    b0 = _bar(minute=0)
    dup = _bar(minute=0)
    # same instrument, close no ascendente
    early_close = _raw_bar(
        timestamp_open=_ts(5),
        timestamp_close=_ts(0) + timedelta(seconds=30),  # <= prev close
    )
    report = validate_bars([b0, dup, early_close])
    codes = {i.code for i in report.issues}
    assert "duplicate_timestamp" in codes
    assert "out_of_order" in codes


# --- sanitize_bars ---


def test_sanitize_keeps_valid_and_merges_ohlcv_issues() -> None:
    kept, report = sanitize_bars([_bar(minute=0), _bar(minute=1, volume="0")])
    assert len(kept) == 2
    assert any(i.code == "empty_bar" for i in report.issues)


def test_sanitize_duplicate_and_ooo_warnings() -> None:
    b0 = _bar(minute=0)
    dup = _bar(minute=0)
    late = _bar(minute=5)
    early = _bar(minute=2)
    kept, report = sanitize_bars([b0, dup, late, early])
    assert len(kept) == 2
    assert any(
        i.code == "duplicate_timestamp" and i.severity is QualitySeverity.WARNING for i in report.issues
    )
    assert any(i.code == "out_of_order" and i.severity is QualitySeverity.WARNING for i in report.issues)
