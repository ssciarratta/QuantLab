"""Tests period → n_bars."""

from __future__ import annotations

from decimal import Decimal

import pytest

from quantlab.brokers.md_limits import LAB_KLINE_HEAVY_WARN, LAB_KLINE_LIMIT_MAX
from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.period_bars import estimate_n_bars, interval_minutes


def test_one_month_1m_within_new_cap() -> None:
    out = estimate_n_bars(period_days=30, interval="1m")
    assert out["n_bars"] == 30 * 24 * 60  # 43200
    assert out["exceeds_lab_cap"] is False
    assert out["lab_kline_limit_max"] == LAB_KLINE_LIMIT_MAX
    assert out["heavy_run"] is True  # > 50k warn


def test_one_month_5m_bars() -> None:
    out = estimate_n_bars(period_days=30, interval="5m")
    assert out["n_bars"] == 30 * 24 * 12  # 8640
    assert out["exceeds_lab_cap"] is False
    assert out["lab_kline_limit_max"] == LAB_KLINE_LIMIT_MAX


def test_one_year_1m_at_cap() -> None:
    out = estimate_n_bars(period_days=365, interval="1m")
    assert out["n_bars"] == 365 * 24 * 60  # 525600
    assert out["exceeds_lab_cap"] is False


def test_two_years_1m_exceeds_cap() -> None:
    out = estimate_n_bars(period_days=730, interval="1m")
    assert out["n_bars"] == 730 * 24 * 60
    assert out["exceeds_lab_cap"] is True


def test_one_year_1d() -> None:
    out = estimate_n_bars(period_days=365, interval="1d")
    assert out["n_bars"] == 365
    assert out["exceeds_lab_cap"] is False
    assert out["heavy_run"] is False


def test_one_year_1h_within_cap() -> None:
    out = estimate_n_bars(period_days=365, interval="1h")
    assert out["n_bars"] == 365 * 24  # 8760
    assert out["exceeds_lab_cap"] is False


def test_interval_minutes_1h() -> None:
    assert interval_minutes("1h") == Decimal("60")


def test_bad_interval() -> None:
    with pytest.raises(ValidationError):
        estimate_n_bars(period_days=1, interval="99x")


def test_heavy_warn_threshold_exported() -> None:
    assert LAB_KLINE_HEAVY_WARN == 40_000
    assert LAB_KLINE_LIMIT_MAX == 525_600
