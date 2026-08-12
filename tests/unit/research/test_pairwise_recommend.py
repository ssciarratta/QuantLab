"""Tests recommend.py — estrategia sugerida pairwise (P4)."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.research.alpha.models import AlphaSignal, SignalDirection, SignalScope
from quantlab.research.alpha.pairwise.recommend import (
    recommend_strategy_for_signal,
    signal_dict_with_recommendation,
)


def _sig(signal_type: str, *, lag: int | None = None) -> AlphaSignal:
    return AlphaSignal(
        signal_id="test-id",
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        signal_type=signal_type,
        scope=SignalScope.PAIR,
        symbols=("BN:BTCUSDT", "BN:ETHUSDT"),
        direction=SignalDirection.LONG_SHORT,
        raw_score=0.8,
        lag=lag,
    )


def test_lagged_correlation_recommends_pairs_trading() -> None:
    rec = recommend_strategy_for_signal("lagged_correlation", lag=3)
    assert rec.strategy_id == "pairs_trading"
    assert "Lag=3" in rec.rationale


def test_cointegration_recommends_cointegration_strategy() -> None:
    rec = recommend_strategy_for_signal("cointegration")
    assert rec.strategy_id == "cointegration"


def test_contemporary_correlation_recommends_momentum() -> None:
    rec = recommend_strategy_for_signal("contemporary_correlation")
    assert rec.strategy_id == "momentum"


def test_signal_dict_includes_recommended_strategy() -> None:
    d = signal_dict_with_recommendation(_sig("pair_spread"))
    assert d["recommended_strategy"]["strategy_id"] == "pairs_trading"
    assert d["metadata"]["recommended_strategy_id"] == "pairs_trading"
