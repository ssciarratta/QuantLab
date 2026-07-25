"""Comisiones dinámicas (Fase 5 — Módulo 2)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantlab.core.types.enums import FeeType, LiquidityType, OrderSide
from quantlab.core.types.validation import require_non_negative


@dataclass(frozen=True, slots=True)
class FeeAssessment:
    """Resultado inmutable de un FeeModel."""

    amount: Decimal
    fee_type: FeeType
    model_id: str

    def __post_init__(self) -> None:
        require_non_negative(self.amount, "amount")


@dataclass(frozen=True, slots=True)
class ZeroFeeModel:
    """Sin comisión — default seguro."""

    model_id: str = "fee.zero.v1"

    def assess(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        liquidity: LiquidityType,
    ) -> FeeAssessment:
        _ = side, price, quantity, liquidity
        return FeeAssessment(amount=Decimal("0"), fee_type=FeeType.OTHER, model_id=self.model_id)


@dataclass(frozen=True, slots=True)
class ProportionalFeeModel:
    """Fee = notional * rate (compat con SimulationConfig.fee_rate)."""

    rate: Decimal
    fee_type: FeeType = FeeType.TAKER
    model_id: str = "fee.proportional.v1"

    def __post_init__(self) -> None:
        require_non_negative(self.rate, "rate")

    def assess(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        liquidity: LiquidityType,
    ) -> FeeAssessment:
        _ = side, liquidity
        notional = price * quantity
        amount = (notional * self.rate).quantize(Decimal("0.00000001"))
        return FeeAssessment(amount=amount, fee_type=self.fee_type, model_id=self.model_id)


@dataclass(frozen=True, slots=True)
class MakerTakerFeeModel:
    """Comisiones diferenciadas maker/taker en basis points."""

    maker_bps: Decimal
    taker_bps: Decimal
    model_id: str = "fee.maker_taker_bps.v1"

    def __post_init__(self) -> None:
        require_non_negative(self.maker_bps, "maker_bps")
        require_non_negative(self.taker_bps, "taker_bps")

    def assess(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        liquidity: LiquidityType,
    ) -> FeeAssessment:
        _ = side
        if liquidity is LiquidityType.MAKER:
            bps = self.maker_bps
            fee_type = FeeType.MAKER
        else:
            bps = self.taker_bps
            fee_type = FeeType.TAKER
        notional = price * quantity
        amount = (notional * bps / Decimal("10000")).quantize(Decimal("0.00000001"))
        return FeeAssessment(amount=amount, fee_type=fee_type, model_id=self.model_id)
