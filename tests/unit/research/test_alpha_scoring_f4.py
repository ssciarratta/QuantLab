"""FASE 4 — CompositeScorer, normalizacion y missing policies."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.types.market import Bar
from quantlab.research.alpha import AlphaScanner
from quantlab.research.alpha.features import FeatureCalculator, FeatureVector
from quantlab.research.alpha.models import MissingFactorPolicy, NormalizationMethod
from quantlab.research.alpha.scoring import (
    CompositeScorer,
    FactorSpec,
    PenaltyEngine,
    min_max_normalize,
    robust_normalize,
)


def _bars(sym: str, n: int = 20, *, trend: bool = True) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i) if trend else Decimal("100")
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


def _fv(
    iid: str,
    *,
    vol: float | None = 0.1,
    volume: float | None = 100.0,
    liq: float | None = 50.0,
    spread: float | None = 0.01,
    vq: float | None = 1.0,
    volq: float | None = 1.0,
) -> FeatureVector:
    return FeatureVector(
        instrument_id=iid,
        volatility=vol,
        volume_score=volume,
        liquidity_score=liq,
        momentum=0.1,
        trend_quality=0.5,
        spread=spread,
        depth=None,
        volume_quality=vq,
        volatility_quality=volq,
        funding=None,
        open_interest=None,
        persistence=None,
        n_bars=20,
        n_live_bars=20,
    )


def test_min_max_and_robust_normalize() -> None:
    vals = [1.0, 2.0, 100.0, None]
    mm = min_max_normalize(vals)
    assert mm[0] == pytest.approx(0.0)
    assert mm[2] == pytest.approx(1.0)
    assert mm[3] is None
    # N=1: neutro 0.5 (antes colapsaba a 0 y rompía moneda puntual)
    solo = min_max_normalize([42.0])
    assert solo == [pytest.approx(0.5)]
    empate = min_max_normalize([3.0, 3.0, 3.0])
    assert empate == [0.0, 0.0, 0.0]
    rob = robust_normalize([1.0, 2.0, 3.0, 100.0])
    assert all(x is not None for x in rob)
    assert min(x for x in rob if x is not None) == pytest.approx(0.0)
    assert max(x for x in rob if x is not None) == pytest.approx(1.0)


def test_scorer_matches_alpha_scanner_legacy_path() -> None:
    bars = {
        "BN:A": _bars("A", 24, trend=True),
        "BN:B": _bars("B", 24, trend=False),
        "BN:C": _bars("C", 24, trend=True),
    }
    bars["BN:C"] = [
        Bar(
            instrument_id="BN:C",
            open=b.open,
            high=b.high,
            low=b.low,
            close=b.close,
            volume=Decimal("5000"),
            timestamp_open=b.timestamp_open,
            timestamp_close=b.timestamp_close,
            timeframe="1h",
        )
        for b in bars["BN:C"]
    ]
    legacy = AlphaScanner().scan(bars, top_n=3, min_bars=3)
    feats = FeatureCalculator().compute_many(bars)
    scored = CompositeScorer(
        missing_policy=MissingFactorPolicy.RENORMALIZE_AVAILABLE,
        apply_quality_penalties=False,
    ).score(feats)
    by_legacy = {s.instrument_id: s for s in legacy.scores}
    by_new = {s.instrument_id: s for s in scored if not s.excluded}
    assert set(by_legacy) == set(by_new)
    for iid, s in by_legacy.items():
        assert by_new[iid].composite == pytest.approx(s.composite, rel=1e-6, abs=1e-8)


def test_exclude_candidate_on_missing() -> None:
    vectors = [_fv("OK"), _fv("BAD", vol=None)]
    scored = CompositeScorer(
        missing_policy=MissingFactorPolicy.EXCLUDE_CANDIDATE,
    ).score(vectors)
    bad = next(r for r in scored if r.instrument_id == "BAD")
    assert bad.excluded is True
    assert "volatility" in bad.exclusion_reason


def test_penalize_missing_applies_penalty() -> None:
    vectors = [_fv("FULL"), _fv("PARTIAL", liq=None, vol=0.5, volume=200.0)]
    scored = CompositeScorer(
        missing_policy=MissingFactorPolicy.PENALIZE_MISSING,
        apply_quality_penalties=False,
        penalty_engine=PenaltyEngine(missing_factor_penalty=0.1),
    ).score(vectors)
    row = next(r for r in scored if r.instrument_id == "PARTIAL")
    assert row.excluded is False
    assert any(p.name == "missing_factors" for p in row.penalties)
    assert row.composite == pytest.approx(max(0.0, row.base_score - 0.1))
    assert row.composite < row.base_score or row.base_score == 0.0


def test_components_expose_weights_and_contributions() -> None:
    scored = CompositeScorer().score([_fv("X", vol=1.0), _fv("Y", vol=0.0)])
    top = scored[0]
    names = {c.name for c in top.components}
    assert names == {"volatility", "volume", "liquidity"}
    assert all(c.contribution is not None for c in top.components if c.available)
    assert top.formula_version
    assert top.normalization_method == NormalizationMethod.MIN_MAX_CROSS_SECTIONAL.value


def test_higher_is_better_false_prefers_tighter_spread() -> None:
    factors = (
        FactorSpec("spread", 1.0, higher_is_better=False, getter=lambda fv: fv.spread),
    )
    scored = CompositeScorer(factors=factors).score(
        [_fv("TIGHT", spread=0.001), _fv("WIDE", spread=0.05)]
    )
    assert scored[0].instrument_id == "TIGHT"
