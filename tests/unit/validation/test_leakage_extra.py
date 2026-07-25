"""Cobertura extra: bordes de validation/leakage.py."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.validation.leakage import LeakageReport, check_temporal_leakage


def _bar(
    *,
    minute: int,
    instrument_id: str = "LEAK:X",
) -> Bar:
    t0 = datetime(2024, 6, 1, tzinfo=UTC) + timedelta(minutes=minute)
    c = Decimal("100")
    return Bar(
        instrument_id=instrument_id,
        open=c,
        high=c + Decimal("1"),
        low=c - Decimal("1"),
        close=c,
        volume=Decimal("1"),
        timestamp_open=t0,
        timestamp_close=t0 + timedelta(minutes=1),
        timeframe="1m",
    )


def test_check_temporal_leakage_ok_no_overlap() -> None:
    train = [_bar(minute=0), _bar(minute=1)]
    test = [_bar(minute=2), _bar(minute=3)]
    report = check_temporal_leakage(train, test)
    assert report == LeakageReport(ok=True, issues=())


def test_check_temporal_leakage_detects_overlap() -> None:
    train = [_bar(minute=0), _bar(minute=2)]
    test = [_bar(minute=1)]
    report = check_temporal_leakage(train, test)
    assert report.ok is False
    assert any("leakage temporal" in issue for issue in report.issues)


def test_check_temporal_leakage_empty_train() -> None:
    report = check_temporal_leakage([], [_bar(minute=0)])
    assert report.ok is False
    assert any("vacíos" in issue for issue in report.issues)


def test_check_temporal_leakage_empty_test() -> None:
    report = check_temporal_leakage([_bar(minute=0)], [])
    assert report.ok is False
    assert any("vacíos" in issue for issue in report.issues)


def test_check_temporal_leakage_both_empty() -> None:
    report = check_temporal_leakage([], [])
    assert report.ok is False
    assert len(report.issues) == 1
    assert "vacíos" in report.issues[0]


def test_check_temporal_leakage_different_instrument() -> None:
    train = [_bar(minute=0, instrument_id="A")]
    test = [_bar(minute=1, instrument_id="B")]
    report = check_temporal_leakage(train, test)
    assert report.ok is False
    assert "instrument_id distinto entre train/test" in report.issues


def test_check_temporal_leakage_overlap_and_instrument() -> None:
    train = [_bar(minute=0, instrument_id="A"), _bar(minute=2, instrument_id="A")]
    test = [_bar(minute=1, instrument_id="B")]
    report = check_temporal_leakage(train, test)
    assert report.ok is False
    assert len(report.issues) == 2
    assert any("leakage temporal" in i for i in report.issues)
    assert "instrument_id distinto entre train/test" in report.issues


def test_check_temporal_leakage_boundary_equal_close_open_ok() -> None:
    """test.open == train.close no es solape estricto (<)."""
    train = [_bar(minute=0)]
    # train close = open+1min; test open exactamente en ese instante
    t_close = train[0].timestamp_close
    test_bar = Bar(
        instrument_id="LEAK:X",
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal("1"),
        timestamp_open=t_close,
        timestamp_close=t_close + timedelta(minutes=1),
        timeframe="1m",
    )
    report = check_temporal_leakage(train, [test_bar])
    assert report.ok is True
    assert report.issues == ()
