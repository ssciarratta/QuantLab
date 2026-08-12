"""IP-1 — contrato AlphaSignal."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from quantlab.research.alpha.models import (
    AlphaSignal,
    FeatureComponent,
    RankedCandidate,
    SignalDirection,
    SignalScope,
)
from quantlab.research.alpha.signals import stable_signal_id


def test_alpha_signal_to_dict_round_trip() -> None:
    ts = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
    sig = AlphaSignal(
        signal_id="abc123",
        timestamp=ts,
        signal_type="lagged_correlation",
        scope=SignalScope.PAIR,
        symbols=("BN:BTCUSDT", "BN:ETHUSDT"),
        direction=SignalDirection.LONG_SHORT,
        raw_score=0.72,
        confidence=0.95,
        lookback=240,
        lag=3,
        timeframe="1h",
        data_quality={"completeness": 0.99},
        metadata={"corr": 0.55},
        normalized_score=0.88,
    )
    raw = sig.to_dict()
    restored = AlphaSignal.from_dict(raw)
    assert restored == sig
    json.dumps(raw)


def test_stable_signal_id_deterministic() -> None:
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    a = stable_signal_id(
        signal_type="cointegration",
        scope=SignalScope.PAIR,
        symbols=("A", "B"),
        timestamp=ts,
        raw_score=1.5,
        lag=None,
        lookback=100,
    )
    b = stable_signal_id(
        signal_type="cointegration",
        scope=SignalScope.PAIR,
        symbols=("B", "A"),
        timestamp=ts,
        raw_score=1.5,
        lag=None,
        lookback=100,
    )
    assert a == b
    assert len(a) == 32


def test_from_ranked_candidate_adapter() -> None:
    ts = datetime(2026, 8, 12, tzinfo=UTC)
    cand = RankedCandidate(
        rank=1,
        venue="binance",
        network="mainnet",
        symbol="BTCUSDT",
        normalized_instrument="BN:BTCUSDT",
        market_type="spot",
        eligible=True,
        composite=0.81,
        base_score=0.81,
        components=(
            FeatureComponent(
                name="volatility",
                raw=0.1,
                normalized=0.8,
                weight=0.35,
                contribution=0.28,
            ),
        ),
    )
    sig = AlphaSignal.from_ranked_candidate(cand, timestamp=ts)
    assert sig.scope == SignalScope.INDIVIDUAL
    assert sig.symbols == ("BN:BTCUSDT",)
    assert sig.raw_score == 0.81
    assert sig.metadata["rank"] == 1
