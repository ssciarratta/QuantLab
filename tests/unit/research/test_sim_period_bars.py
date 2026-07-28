"""Tests period → n_bars."""

from __future__ import annotations

from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.period_bars import estimate_n_bars, interval_minutes


def test_one_month_5m_bars() -> None:
    out = estimate_n_bars(period_days=30, interval="5m")
    assert out["n_bars"] == 30 * 24 * 12  # 8640
    assert out["exceeds_lab_cap_3000"] is True


def test_one_year_1d() -> None:
    out = estimate_n_bars(period_days=365, interval="1d")
    assert out["n_bars"] == 365
    assert out["exceeds_lab_cap_3000"] is False


def test_interval_minutes_1h() -> None:
    assert interval_minutes("1h") == Decimal("60")


def test_bad_interval() -> None:
    with pytest.raises(ValidationError):
        estimate_n_bars(period_days=1, interval="99x")
