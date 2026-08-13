"""Tests identidad de oportunidad y helpers temporales."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.research.alpha.models import AlphaSignal, SignalDirection, SignalScope
from quantlab.research.alpha.opportunity import (
    effective_embargo_bars,
    make_opportunity_id,
    periods_per_year_for_timeframe,
    ranking_b_status,
)


def _sig() -> AlphaSignal:
    return AlphaSignal(
        signal_id="sig-a",
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        signal_type="legacy_v1",
        scope=SignalScope.INDIVIDUAL,
        symbols=("BN:BTCUSDT",),
        direction=SignalDirection.LONG,
        raw_score=0.5,
        timeframe="1h",
        lookback=24,
    )


def test_opportunity_id_stable() -> None:
    a = make_opportunity_id(signal=_sig(), scan_id="scan_1", venue="binance")
    b = make_opportunity_id(signal=_sig(), scan_id="scan_1", venue="binance")
    assert a == b
    assert a.startswith("opp_")
    c = make_opportunity_id(signal=_sig(), scan_id="scan_2", venue="binance")
    assert a != c


def test_periods_and_embargo() -> None:
    assert periods_per_year_for_timeframe("1h") == 8760.0
    assert periods_per_year_for_timeframe("1d") == 365.0
    assert effective_embargo_bars(requested=2, lookback=0) == 2
    assert effective_embargo_bars(requested=2, lookback=12) == 8
    assert effective_embargo_bars(requested=2, lookback=100) == 2
    # 24 barras / 70% train: no puede subir embargo y dejar el test vacío
    assert effective_embargo_bars(requested=2, lookback=24, n_bars=24) == 2


def test_ranking_b_status() -> None:
    assert ranking_b_status(validated=True, ok=True) == "validated_historically"
    assert ranking_b_status(validated=False, ok=True) == "rejected"
    assert ranking_b_status(validated=False, ok=False) == "failed"
