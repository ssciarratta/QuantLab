"""Construcción determinista de barras OHLCV desde trades."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar, Trade
from quantlab.data.exchanges.a3.constants import BAR_TIMEFRAMES
from quantlab.data.exchanges.a3.exceptions import A3DataError

_TIMEFRAME_DELTA: dict[str, timedelta] = {
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
}


@dataclass(frozen=True, slots=True)
class BarBuildReport:
    bars: tuple[Bar, ...]
    duplicate_trades_removed: int
    gaps: tuple[str, ...]
    incomplete_last_bar: bool


def _bucket_start(ts: datetime, delta: timedelta) -> datetime:
    if ts.tzinfo is None:
        raise A3DataError("trade timestamp naive")
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    aware = ts.astimezone(UTC)
    seconds = int((aware - epoch).total_seconds())
    step = int(delta.total_seconds())
    bucket = seconds - (seconds % step)
    return epoch + timedelta(seconds=bucket)


def trade_dedupe_key(trade: Trade) -> str:
    return f"{trade.trade_id}|{trade.timestamp.isoformat()}|{trade.price}|{trade.quantity}"


def build_bars_from_trades(
    trades: list[Trade],
    *,
    timeframe: str,
    instrument_id: str,
    now: datetime | None = None,
) -> BarBuildReport:
    if timeframe not in BAR_TIMEFRAMES:
        raise A3DataError(f"timeframe no soportado: {timeframe}")
    delta = _TIMEFRAME_DELTA[timeframe]
    # Orden + dedupe
    ordered = sorted(trades, key=lambda t: (t.timestamp, t.trade_id, str(t.price), str(t.quantity)))
    seen: set[str] = set()
    unique: list[Trade] = []
    dupes = 0
    for trade in ordered:
        key = trade_dedupe_key(trade)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        unique.append(trade)

    buckets: dict[datetime, list[Trade]] = {}
    for trade in unique:
        if trade.instrument_id != instrument_id:
            raise A3DataError(f"trade.instrument_id={trade.instrument_id!r} != {instrument_id!r}")
        start = _bucket_start(trade.timestamp, delta)
        buckets.setdefault(start, []).append(trade)

    bars: list[Bar] = []
    gaps: list[str] = []
    starts = sorted(buckets)
    for i, start in enumerate(starts):
        chunk = buckets[start]
        prices = [t.price for t in chunk]
        volume = sum((t.quantity for t in chunk), Decimal("0"))
        end = start + delta
        bars.append(
            Bar(
                instrument_id=instrument_id,
                open=prices[0],
                high=max(prices),
                low=min(prices),
                close=prices[-1],
                volume=volume,
                timestamp_open=start,
                timestamp_close=end,
                timeframe=timeframe,
            )
        )
        if i > 0:
            prev = starts[i - 1]
            expected = prev + delta
            if start > expected:
                gaps.append(f"{expected.isoformat()}->{start.isoformat()}")

    incomplete = False
    ref = now or datetime.now(tz=UTC)
    if bars and bars[-1].timestamp_close > ref:
        incomplete = True

    return BarBuildReport(
        bars=tuple(bars),
        duplicate_trades_removed=dupes,
        gaps=tuple(gaps),
        incomplete_last_bar=incomplete,
    )
