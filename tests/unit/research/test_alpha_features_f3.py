"""FASE 3 — FeatureCalculator modular (ausencia → None)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.types.market import Bar
from quantlab.research.alpha import AlphaScanner
from quantlab.research.alpha.features import FeatureCalculator, MarketExtras


def _bars(sym: str, n: int = 24, *, trend: bool = True) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i) if trend else Decimal(100)
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"BN:{sym}",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("0.5"),
                close=c,
                volume=Decimal("1000"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


def test_missing_book_funding_oi_are_none_not_zero() -> None:
    fv = FeatureCalculator().compute("BN:AAA", _bars("AAA", 16))
    assert fv.funding is None
    assert fv.open_interest is None
    assert fv.depth is None
    assert fv.available_map()["funding"] is False
    assert fv.available_map()["depth"] is False
    assert fv.momentum is not None
    assert fv.trend_quality is not None
    assert fv.spread is not None  # proxy HL/C


def test_book_spread_uses_bid_ask_when_present() -> None:
    fv = FeatureCalculator().compute(
        "BN:AAA",
        _bars("AAA", 8),
        extras=MarketExtras(best_bid=99.0, best_ask=101.0, depth_notional=50000.0),
    )
    assert fv.spread == pytest.approx(0.02)
    assert fv.depth == 50000.0


def test_legacy_features_match_alpha_scanner() -> None:
    bars = {"BN:A": _bars("A", 20), "BN:B": _bars("B", 20, trend=False)}
    scan = AlphaScanner().scan(bars, top_n=2, min_bars=3)
    feats = FeatureCalculator().compute_many(bars)
    by_id = {s.instrument_id: s for s in scan.scores}
    for iid, fv in feats.items():
        s = by_id[iid]
        assert fv.volatility == pytest.approx(s.volatility)
        assert fv.volume_score == pytest.approx(s.volume_score)
        assert fv.liquidity_score == pytest.approx(s.liquidity_score)


def test_empty_bars_all_core_none() -> None:
    fv = FeatureCalculator().compute("BN:EMPTY", [])
    assert fv.volatility is None
    assert fv.volume_score is None
    assert fv.liquidity_score is None
    assert fv.momentum is None
    assert fv.n_bars == 0
