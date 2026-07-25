"""Modelos de deslizamiento (slippage) — Decimal only."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import OrderSide
from quantlab.core.types.market import Bar
from quantlab.core.types.validation import require_non_negative


@dataclass(frozen=True, slots=True)
class NoSlippageModel:
    """Identidad — compatibilidad total con fills Fase 4."""

    model_id: str = "slippage.none.v1"

    def apply(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        bar: Bar,
    ) -> Decimal:
        return price


@dataclass(frozen=True, slots=True)
class FixedSlippageModel:
    """Slippage fijo en basis points, siempre adverso al trader.

    BUY → precio * (1 + bps/10000)
    SELL → precio * (1 - bps/10000)
    """

    bps: Decimal
    max_slippage_bps: Decimal | None = None
    model_id: str = "slippage.fixed_bps.v1"

    def __post_init__(self) -> None:
        require_non_negative(self.bps, "bps")
        if self.bps >= Decimal("10000"):
            raise ValidationError("bps debe ser < 10000 (evita precio SELL <= 0)")
        if self.max_slippage_bps is not None:
            require_non_negative(self.max_slippage_bps, "max_slippage_bps")
            if self.max_slippage_bps >= Decimal("10000"):
                raise ValidationError("max_slippage_bps debe ser < 10000")
            if self.bps > self.max_slippage_bps:
                raise ValidationError("bps no puede exceder max_slippage_bps")

    def apply(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        bar: Bar,
    ) -> Decimal:
        _ = quantity, bar
        effective = self.bps
        if self.max_slippage_bps is not None and effective > self.max_slippage_bps:
            effective = self.max_slippage_bps
        factor = effective / Decimal("10000")
        if side is OrderSide.BUY:
            return price * (Decimal("1") + factor)
        return price * (Decimal("1") - factor)


@dataclass(frozen=True, slots=True)
class VolumeShareSlippageModel:
    """Impacto proporcional a quantity / bar.volume.

    slippage_bps = min(max_slippage_bps, impact_bps * share)
    share = quantity / volume (si volume == 0 → max_slippage_bps).
    """

    impact_bps: Decimal
    max_slippage_bps: Decimal
    model_id: str = "slippage.volume_share.v1"

    def __post_init__(self) -> None:
        require_non_negative(self.impact_bps, "impact_bps")
        require_non_negative(self.max_slippage_bps, "max_slippage_bps")
        if self.max_slippage_bps >= Decimal("10000"):
            raise ValidationError("max_slippage_bps debe ser < 10000")

    def apply(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        bar: Bar,
    ) -> Decimal:
        share = Decimal("1") if bar.volume <= 0 else quantity / bar.volume
        raw_bps = self.impact_bps * share
        effective = min(raw_bps, self.max_slippage_bps)
        factor = effective / Decimal("10000")
        if side is OrderSide.BUY:
            return price * (Decimal("1") + factor)
        return price * (Decimal("1") - factor)
