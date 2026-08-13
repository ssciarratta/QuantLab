"""Tests pipeline Alpha v3 — individual signals + validate_candidate."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.research.alpha.individual_export import (
    attach_individual_signals,
    scores_to_ranked_signals,
)
from quantlab.research.alpha.models import AlphaSignal, SignalDirection, SignalScope
from quantlab.research.alpha.validation.pipeline import ValidationPipeline
from quantlab.research.alpha.validation.trial_ledger import TrialLedger
from quantlab.research.alpha.validation.validate_candidate import (
    default_trials_path,
    equity_curve_to_returns,
    list_validated_from_ledger,
    validate_candidate,
)


def test_equity_curve_to_returns() -> None:
    assert equity_curve_to_returns([100.0, 110.0, 99.0])[0] == pytest.approx(0.1)


def test_scores_to_signals_and_no_leakage() -> None:
    scores = [
        {
            "instrument_id": "BN:BTCUSDT",
            "composite": 0.9,
            "components": [
                {"name": "volatility", "raw": 1.0, "available": True},
                {"name": "volume", "raw": 0.5, "available": True},
            ],
        },
        {
            "instrument_id": "BN:ETHUSDT",
            "composite": 0.2,
            "components": [
                {"name": "volatility", "raw": 0.1, "available": True},
                {"name": "volume", "raw": None, "available": False},
            ],
        },
    ]
    sigs = scores_to_ranked_signals(scores, profile="legacy_v1", timeframe="1h", lookback=24)
    assert len(sigs) == 2
    assert sigs[0].scope is SignalScope.INDIVIDUAL
    assert sigs[0].normalized_score is not None
    assert sigs[0].normalized_score >= sigs[1].normalized_score  # type: ignore[operator]
    assert sigs[0].confidence is not None

    with pytest.raises(ValidationError, match="leakage"):
        ValidationPipeline().assert_no_selection_leakage(
            selection_scores={"composite": 1.0, "sharpe": 2.0}
        )


def test_attach_individual_signals() -> None:
    payload = {
        "ok": True,
        "profile": "momentum",
        "interval": "1h",
        "kline_limit": 100,
        "top_n": 1,
        "scores": [{"instrument_id": "BN:SOLUSDT", "composite": 0.7}],
        "note": "test",
    }
    out = attach_individual_signals(payload)
    assert out["signal_scope"] == "individual"
    assert len(out["signals"]) == 1
    assert out["signals"][0]["scope"] == "individual"


def test_trial_ledger_persists_wins_and_losses(tmp_path: Path) -> None:
    path = default_trials_path(tmp_path)
    led = TrialLedger(path=path)
    led.log(
        trial_id="t1",
        detector_id="validate_candidate",
        signal_type="legacy_v1",
        symbols=("BN:A",),
        metadata={
            "phase": "validation",
            "strategy_id": "momentum",
            "validated": True,
            "deflated_sharpe": 0.99,
            "sharpe_net": 1.2,
        },
    )
    led.log(
        trial_id="t2",
        detector_id="validate_candidate",
        signal_type="legacy_v1",
        symbols=("BN:B",),
        metadata={
            "phase": "validation",
            "strategy_id": "momentum",
            "validated": False,
            "deflated_sharpe": 0.1,
            "sharpe_net": -0.5,
            "ok": True,
        },
    )
    assert path.is_file()
    led2 = TrialLedger(path=path)
    assert led2.count() == 2
    ranked = list_validated_from_ledger(led2)
    assert len(ranked) == 1
    assert ranked[0]["strategy_id"] == "momentum"
    from quantlab.research.alpha.validation.validate_candidate import list_ranking_b_from_ledger

    all_b = list_ranking_b_from_ledger(led2)
    assert len(all_b) == 2
    statuses = {r["status"] for r in all_b}
    assert "validated_historically" in statuses
    assert "rejected" in statuses


def _bars(iid: str, n: int = 80) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 1, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=iid,
                open=c,
                high=c + 1,
                low=c - 1,
                close=c,
                volume=Decimal(1000),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


def test_validate_candidate_always_logs(tmp_path: Path) -> None:
    path = default_trials_path(tmp_path)
    sig = AlphaSignal(
        signal_id="sig-1",
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        signal_type="legacy_v1",
        scope=SignalScope.INDIVIDUAL,
        symbols=("BN:BTCUSDT",),
        direction=SignalDirection.LONG,
        raw_score=0.5,
        timeframe="1h",
    )
    r1 = validate_candidate(
        sig,
        strategy_id="momentum",
        bars=_bars("BN:BTCUSDT", 80),
        ledger_path=path,
    )
    r2 = validate_candidate(
        sig,
        strategy_id="pairs_trading",
        bars=_bars("BN:BTCUSDT", 80),
        ledger_path=path,
    )
    led = TrialLedger(path=path)
    assert led.count() >= 2
    assert r1.n_trials_at_eval >= 1
    assert r2.n_trials_at_eval >= 2
    assert "strategy_id" in r1.to_dict()
    assert r1.opportunity_id
    assert r1.to_dict()["opportunity_id"] == r1.opportunity_id
    assert r1.status in ("validated_historically", "rejected", "failed")
