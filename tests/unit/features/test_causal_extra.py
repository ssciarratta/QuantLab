"""Cobertura extra: gaps de assert_bars_causal_ready y causal_window."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.features.causal import assert_bars_causal_ready, causal_window


def _bars(n: int, *, instrument_id: str = "CAUSAL:X") -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 5, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id=instrument_id,
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal(10 + i),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_assert_ready_rejects_min_lookback_zero() -> None:
    with pytest.raises(ValidationError, match="min_lookback inválido"):
        assert_bars_causal_ready(_bars(3), min_lookback=0)


def test_assert_ready_rejects_min_lookback_negative() -> None:
    with pytest.raises(ValidationError, match="min_lookback inválido"):
        assert_bars_causal_ready(_bars(3), min_lookback=-1)


def test_assert_ready_rejects_insufficient_bars() -> None:
    with pytest.raises(ValidationError, match="se requieren al menos 5"):
        assert_bars_causal_ready(_bars(4), min_lookback=5)


def test_assert_ready_ok_exact_min_lookback() -> None:
    assert_bars_causal_ready(_bars(3), min_lookback=3)


def test_assert_ready_rejects_mixed_instruments() -> None:
    bars = _bars(2, instrument_id="A")
    other = _bars(1, instrument_id="B")[0]
    with pytest.raises(ValidationError, match="instrument_id"):
        assert_bars_causal_ready([bars[0], other], min_lookback=1)


def test_assert_ready_rejects_descending_close() -> None:
    bars = _bars(2)
    swapped = [bars[1], bars[0]]
    with pytest.raises(ValidationError, match="estrictamente ordenadas"):
        assert_bars_causal_ready(swapped, min_lookback=1)


def test_causal_window_happy_path_slice() -> None:
    bars = _bars(5)
    window = causal_window(bars, index=3, lookback=3)
    assert list(window) == bars[1:4]
    assert len(window) == 3


def test_causal_window_lookback_one_at_zero() -> None:
    bars = _bars(2)
    window = causal_window(bars, index=0, lookback=1)
    assert list(window) == [bars[0]]


def test_causal_window_rejects_negative_index() -> None:
    with pytest.raises(ValidationError, match="índice fuera de rango"):
        causal_window(_bars(3), index=-1, lookback=1)


def test_causal_window_rejects_index_past_end() -> None:
    bars = _bars(3)
    with pytest.raises(ValidationError, match="índice fuera de rango"):
        causal_window(bars, index=3, lookback=1)


def test_causal_window_rejects_lookback_zero() -> None:
    with pytest.raises(ValidationError, match="lookback inválido"):
        causal_window(_bars(3), index=1, lookback=0)


def test_causal_window_rejects_lookback_negative() -> None:
    with pytest.raises(ValidationError, match="lookback inválido"):
        causal_window(_bars(3), index=1, lookback=-2)


def test_causal_window_rejects_incomplete_mid_series() -> None:
    bars = _bars(4)
    with pytest.raises(ValidationError, match="ventana causal incompleta"):
        causal_window(bars, index=1, lookback=3)
