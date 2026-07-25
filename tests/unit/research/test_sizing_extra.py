"""Bordes extra de position sizing (distintos de test_auto_audit_remediation)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.research.sizing import fixed_fractional, volatility_target


def test_volatility_target_scales_up_when_realized_below_target() -> None:
    qty = volatility_target(
        Decimal("5000"),
        target_vol=Decimal("0.20"),
        realized_vol=Decimal("0.10"),
        base_qty=Decimal("3"),
    )
    assert qty == Decimal("6.00000000")


def test_volatility_target_identity_when_vols_equal() -> None:
    qty = volatility_target(
        Decimal("1000"),
        target_vol=Decimal("0.15"),
        realized_vol=Decimal("0.15"),
        base_qty=Decimal("4.5"),
    )
    assert qty == Decimal("4.50000000")


@pytest.mark.parametrize(
    ("equity", "target_vol", "realized_vol", "base_qty"),
    [
        (Decimal("0"), Decimal("0.1"), Decimal("0.1"), Decimal("1")),
        (Decimal("1000"), Decimal("0"), Decimal("0.1"), Decimal("1")),
        (Decimal("1000"), Decimal("0.1"), Decimal("0"), Decimal("1")),
        (Decimal("1000"), Decimal("0.1"), Decimal("0.1"), Decimal("0")),
        (Decimal("-1"), Decimal("0.1"), Decimal("0.1"), Decimal("1")),
    ],
)
def test_volatility_target_rejects_non_positive(
    equity: Decimal,
    target_vol: Decimal,
    realized_vol: Decimal,
    base_qty: Decimal,
) -> None:
    with pytest.raises(ValidationError):
        volatility_target(
            equity,
            target_vol=target_vol,
            realized_vol=realized_vol,
            base_qty=base_qty,
        )


def test_fixed_fractional_quantizes_fractional_qty() -> None:
    qty = fixed_fractional(
        Decimal("100"),
        risk_fraction=Decimal("0.03"),
        stop_distance=Decimal("7"),
    )
    # (100 * 0.03) / 7 = 0.428571... → 8 dp
    assert qty == Decimal("0.42857143")


@pytest.mark.parametrize(
    ("equity", "risk_fraction", "stop_distance"),
    [
        (Decimal("0"), Decimal("0.01"), Decimal("1")),
        (Decimal("1000"), Decimal("0"), Decimal("1")),
        (Decimal("1000"), Decimal("0.01"), Decimal("0")),
        (Decimal("-10"), Decimal("0.01"), Decimal("1")),
    ],
)
def test_fixed_fractional_rejects_non_positive(
    equity: Decimal,
    risk_fraction: Decimal,
    stop_distance: Decimal,
) -> None:
    with pytest.raises(ValidationError):
        fixed_fractional(equity, risk_fraction=risk_fraction, stop_distance=stop_distance)


def test_fixed_fractional_rejects_risk_fraction_above_one() -> None:
    with pytest.raises(ValidationError, match="risk_fraction debe ser < 1"):
        fixed_fractional(
            Decimal("1000"),
            risk_fraction=Decimal("1.5"),
            stop_distance=Decimal("1"),
        )
