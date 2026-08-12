"""Tests cointegración + validación + pair backtest."""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.backtester.pair_engine import run_spread_backtest
from quantlab.core.types.market import Bar
from quantlab.research.alpha.detectors.base import DetectorContext, DetectorRunConfig
from quantlab.research.alpha.detectors.cointegration import CointegrationDetector
from quantlab.research.alpha.detectors.registry import DetectorRegistry
from quantlab.research.alpha.models import AlphaSignal, SignalDirection, SignalScope
from quantlab.research.alpha.pairwise.stats import adf_pvalue_proxy, half_life_bars, log_spread
from quantlab.research.alpha.validation.deflated_sharpe import deflated_sharpe_ratio
from quantlab.research.alpha.validation.pipeline import ValidationPipeline
from quantlab.research.alpha.validation.trial_ledger import TrialLedger


def _bars(iid: str, closes: list[float]) -> tuple[Bar, ...]:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
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


def _cointegrated_pair(n: int = 200) -> tuple[list[float], list[float]]:
    random.seed(7)
    rw = [0.0]
    for _ in range(n - 1):
        rw.append(rw[-1] + random.gauss(0, 0.02))
    a = [100.0 * math.exp(rw[i] + random.gauss(0, 0.002)) for i in range(n)]
    b = [50.0 * math.exp(0.5 * rw[i] + random.gauss(0, 0.002)) for i in range(n)]
    return a, b


def test_adf_proxy_stationary_spread() -> None:
    a, b = _cointegrated_pair(250)
    spread = log_spread(a, b, beta=2.0)
    pval = adf_pvalue_proxy(spread)
    assert pval < 0.5


def test_cointegration_detector_finds_pair() -> None:
    a, b = _cointegrated_pair(200)
    universe = {"WB:A": _bars("WB:A", a), "WB:B": _bars("WB:B", b)}
    reg = DetectorRegistry()
    reg.register(CointegrationDetector())
    ctx = DetectorContext(
        bars_by_instrument=universe,
        timeframe="1h",
        lookback_bars=120,
        venue="lab",
        market_type="synthetic",
        config={"min_bars": 120, "max_pairs": 5, "adf_max_p": 0.20, "min_half_life": 0.01},
    )
    signals = reg.run_all(ctx, DetectorRunConfig(enabled=("cointegration",)))
    assert len(signals) >= 1
    assert signals[0].metadata.get("hedge_ratio") is not None


def test_trial_ledger_and_deflated_sharpe() -> None:
    ledger = TrialLedger()
    for i in range(50):
        ledger.log(
            trial_id=f"t{i}",
            detector_id="lagged_correlation",
            signal_type="lagged_correlation",
            symbols=("A", "B"),
            lag=i % 5,
        )
    assert ledger.count() == 50
    dsr = deflated_sharpe_ratio(1.5, n_trials=50, n_observations=200)
    assert 0.0 <= dsr <= 1.0
    assert dsr < 1.0


def test_validation_pipeline_separates_phases() -> None:
    pipe = ValidationPipeline()
    pipe.assert_no_selection_leakage(selection_scores={"composite": 0.8, "volatility": 0.3})
    sig = AlphaSignal(
        signal_id="s1",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        signal_type="pair_spread",
        scope=SignalScope.PAIR,
        symbols=("A", "B"),
        direction=SignalDirection.LONG_SHORT,
        raw_score=2.1,
    )
    rets = tuple(0.001 * (1 if i % 2 == 0 else -1) for i in range(100))
    ev = pipe.evaluate_backtest(sig, net_returns=rets, periods_per_year=8760.0)
    assert ev.n_returns == 100


def test_spread_backtest_mean_reversion() -> None:
    random.seed(3)
    n = 300
    spread_rw = [0.0]
    for _ in range(n - 1):
        spread_rw.append(spread_rw[-1] * 0.95 + random.gauss(0, 0.02))
    a = [100.0 * math.exp(s) for s in spread_rw]
    b = [100.0] * n
    bt = run_spread_backtest(tuple(a), tuple(b), entry_z=1.5, exit_z=0.3, fee_bps_per_leg=5.0)
    assert len(bt.net_returns) > 0
