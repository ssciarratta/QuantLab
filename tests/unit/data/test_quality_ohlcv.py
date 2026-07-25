"""Guardias OHLCV y sanitize_bars."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.data.quality import QualitySeverity, sanitize_bars, validate_bars


def _bar(
    *,
    open_: str = "10",
    high: str = "11",
    low: str = "9",
    close: str = "10.5",
    volume: str = "1",
    minute: int = 0,
) -> Bar:
    t0 = datetime(2024, 1, 1, tzinfo=UTC) + timedelta(minutes=minute)
    return Bar(
        instrument_id="X",
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


def test_validate_bars_ok() -> None:
    report = validate_bars([_bar(), _bar(minute=1, open_="10.5", high="12", low="10", close="11")])
    assert not report.has_error


def test_sanitize_drops_duplicates_and_unordered() -> None:
    b0 = _bar()
    dup = _bar()
    late = _bar(minute=5)
    early = _bar(minute=2)  # tras late quedaría desordenado si se inserta mal
    kept, report = sanitize_bars([b0, dup, late, early])
    assert len(kept) == 2
    assert any(i.code == "duplicate_timestamp" for i in report.issues)
    assert any(i.severity is QualitySeverity.WARNING for i in report.issues)
