"""Adaptación Bar QuantLab → OHLCV(+amount) para Kronos (stdlib only)."""

from __future__ import annotations

import math
from collections.abc import Sequence

from quantlab.core.types.market import Bar
from quantlab.research.alpha.kronos.errors import KronosError, KronosSkipReason
from quantlab.research.alpha.kronos.protocol import ForecastRequest


def bars_to_ohlcva(bars: Sequence[Bar]) -> dict[str, tuple[float, ...] | tuple[int, ...]]:
    if not bars:
        raise KronosError(KronosSkipReason.INSUFFICIENT_BARS, "serie vacía")
    opens: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    volumes: list[float] = []
    amounts: list[float] = []
    ts: list[int] = []
    for i, b in enumerate(bars):
        o = float(b.open)
        h = float(b.high)
        l_ = float(b.low)
        c = float(b.close)
        v = float(b.volume)
        if not all(math.isfinite(x) for x in (o, h, l_, c, v)) or min(o, h, l_, c) <= 0:
            raise KronosError(
                KronosSkipReason.INVALID_OHLCV,
                f"OHLCV inválido en idx={i} instrument={b.instrument_id}",
            )
        opens.append(o)
        highs.append(h)
        lows.append(l_)
        closes.append(c)
        vol = max(0.0, v)
        volumes.append(vol)
        typical = (h + l_ + c) / 3.0
        amounts.append(vol * typical)
        ts.append(int(b.timestamp_close.timestamp() * 1e9))
    return {
        "open": tuple(opens),
        "high": tuple(highs),
        "low": tuple(lows),
        "close": tuple(closes),
        "volume": tuple(volumes),
        "amount": tuple(amounts),
        "timestamps_ns": tuple(ts),
    }


def build_forecast_request(
    instrument_id: str,
    bars: Sequence[Bar],
    *,
    lookback: int,
    pred_len: int,
    sample_count: int,
    temperature: float,
    top_p: float,
    seed: int,
) -> ForecastRequest:
    """Usa solo el tramo de ranking (caller debe pasar rank_bars, nunca OOS)."""
    if len(bars) < max(8, min(lookback, 16)):
        raise KronosError(
            KronosSkipReason.INSUFFICIENT_BARS,
            f"necesita >= lookback efectivo; got={len(bars)} lookback={lookback}",
        )
    window = list(bars)[-lookback:] if len(bars) > lookback else list(bars)
    arr = bars_to_ohlcva(window)
    return ForecastRequest(
        instrument_id=instrument_id,
        lookback_opens=arr["open"],  # type: ignore[arg-type]
        lookback_highs=arr["high"],  # type: ignore[arg-type]
        lookback_lows=arr["low"],  # type: ignore[arg-type]
        lookback_closes=arr["close"],  # type: ignore[arg-type]
        lookback_volumes=arr["volume"],  # type: ignore[arg-type]
        lookback_amounts=arr["amount"],  # type: ignore[arg-type]
        timestamps_ns=arr["timestamps_ns"],  # type: ignore[arg-type]
        pred_len=pred_len,
        sample_count=sample_count,
        temperature=temperature,
        top_p=top_p,
        seed=seed,
    )


__all__ = ["bars_to_ohlcva", "build_forecast_request"]
