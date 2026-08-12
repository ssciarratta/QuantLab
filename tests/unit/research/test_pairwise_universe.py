"""Tests pairwise universe + lagged correlation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.research.alpha.detectors.base import DetectorContext, DetectorRunConfig
from quantlab.research.alpha.detectors.lagged_correlation import (
    LaggedCorrelationDetector,
    benjamini_hochberg,
)
from quantlab.research.alpha.detectors.registry import DetectorRegistry
from quantlab.research.alpha.normalization import percentile_rank_signals
from quantlab.research.alpha.pairwise.align import align_pair_bars
from quantlab.research.alpha.pairwise.universe import generate_pair_candidates


def _bars(
    iid: str,
    closes: list[float],
    *,
    start: datetime | None = None,
) -> tuple[Bar, ...]:
    t0 = start or datetime(2026, 1, 1, tzinfo=UTC)
    out: list[Bar] = []
    for i, c in enumerate(closes):
        ts_o = t0 + timedelta(hours=i)
        ts_c = t0 + timedelta(hours=i + 1)
        out.append(
            Bar(
                instrument_id=iid,
                open=Decimal(str(c)),
                high=Decimal(str(c)),
                low=Decimal(str(c)),
                close=Decimal(str(c)),
                volume=Decimal("1000"),
                timestamp_open=ts_o,
                timestamp_close=ts_c,
                timeframe="1h",
            )
        )
    return tuple(out)


def test_generate_pair_candidates_caps() -> None:
    universe = {f"WB:{x}": _bars(f"WB:{x}", [1.0] * 60) for x in ("A", "B", "C", "D")}
    pairs = generate_pair_candidates(universe, max_pairs=2, min_bars=50)
    assert len(pairs) == 2


def test_align_pair_bars_inner_join() -> None:
    a = _bars("WB:A", [1, 2, 3, 4, 5])
    b = _bars("WB:B", [10, 11, 12, 13, 14])
    aligned = align_pair_bars(a, b)
    assert aligned is not None
    assert len(aligned.closes_a) == 5


def test_benjamini_hochberg_rejects_smallest_p() -> None:
    mask = benjamini_hochberg([0.001, 0.5, 0.8], alpha=0.10)
    assert mask[0] is True
    assert mask[1] is False


def test_lagged_correlation_synthetic_lag() -> None:
    """B sigue a A con retorno correlacionado (lag 2 proxy via construction)."""
    n = 120
    a_closes = [100.0]
    b_closes = [200.0]
    for i in range(1, n):
        shock = 0.01 * ((i % 7) - 3)
        a_closes.append(a_closes[-1] * (1 + shock))
        # B imita A con 2 pasos de delay
        if i >= 2:
            b_closes.append(b_closes[-1] * (1 + shock * 0.9))
        else:
            b_closes.append(b_closes[-1])

    universe = {
        "WB:A": _bars("WB:A", a_closes),
        "WB:B": _bars("WB:B", b_closes),
    }
    reg = DetectorRegistry()
    reg.register(LaggedCorrelationDetector())
    ctx = DetectorContext(
        bars_by_instrument=universe,
        timeframe="1h",
        lookback_bars=80,
        venue="lab",
        market_type="synthetic",
        config={"min_bars": 80, "max_pairs": 10, "lags": [0, 1, 2, 3], "fdr_alpha": 0.25},
    )
    signals = reg.run_all(ctx, DetectorRunConfig(enabled=("lagged_correlation",)))
    assert signals, "expected at least one lagged correlation signal"
    assert all(s.scope.value == "pair" for s in signals)


def test_percentile_rank_by_scope() -> None:
    from quantlab.research.alpha.models import AlphaSignal, SignalDirection, SignalScope

    ts = datetime(2026, 8, 12, tzinfo=UTC)
    s1 = AlphaSignal(
        signal_id="1",
        timestamp=ts,
        signal_type="x",
        scope=SignalScope.PAIR,
        symbols=("A", "B"),
        direction=SignalDirection.LONG_SHORT,
        raw_score=0.2,
        timeframe="1h",
    )
    s2 = AlphaSignal(
        signal_id="2",
        timestamp=ts,
        signal_type="x",
        scope=SignalScope.PAIR,
        symbols=("C", "D"),
        direction=SignalDirection.LONG_SHORT,
        raw_score=0.8,
        timeframe="1h",
    )
    ranked = percentile_rank_signals((s1, s2))
    scores = {s.signal_id: s.normalized_score for s in ranked}
    assert scores["1"] == 0.0
    assert scores["2"] == 1.0
