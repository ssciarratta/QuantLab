"""Órdenes, intenciones, fills y fees."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import (
    FeeType,
    IntentType,
    LiquidityType,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from quantlab.core.types.validation import (
    require_aware,
    require_non_empty_str,
    require_non_negative,
    require_positive,
)


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """Intención de la estrategia — no implica ejecución."""

    intent_id: str
    intent_type: IntentType
    instrument_id: str
    side: OrderSide | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None
    order_type: OrderType | None = None
    time_in_force: TimeInForce | None = None
    replace_target_id: str | None = None

    def __post_init__(self) -> None:
        require_non_empty_str(self.intent_id, "intent_id")
        require_non_empty_str(self.instrument_id, "instrument_id")

        if self.intent_type is IntentType.NO_ACTION:
            if any(
                v is not None
                for v in (
                    self.side,
                    self.quantity,
                    self.price,
                    self.order_type,
                    self.time_in_force,
                    self.replace_target_id,
                )
            ):
                raise ValidationError("NO_ACTION no admite campos de orden")
            return

        if self.intent_type is IntentType.CANCEL_ORDER:
            require_non_empty_str(self.replace_target_id, "replace_target_id")
            if any(
                v is not None
                for v in (self.side, self.quantity, self.price, self.order_type, self.time_in_force)
            ):
                raise ValidationError("CANCEL_ORDER no admite campos de place/replace")
            return

        if self.intent_type is IntentType.REPLACE_ORDER:
            require_non_empty_str(self.replace_target_id, "replace_target_id")
            self._validate_place_like_fields()
            return

        if self.intent_type is IntentType.PLACE_ORDER:
            if self.replace_target_id is not None:
                raise ValidationError("PLACE_ORDER no admite replace_target_id")
            self._validate_place_like_fields()
            return

        raise ValidationError(f"intent_type no soportado: {self.intent_type}")

    def _validate_place_like_fields(self) -> None:
        if self.side is None:
            raise ValidationError("side es obligatorio")
        if self.order_type is None:
            raise ValidationError("order_type es obligatorio")
        if self.quantity is None:
            raise ValidationError("quantity es obligatorio")
        require_positive(self.quantity, "quantity")
        if self.order_type is OrderType.LIMIT:
            if self.price is None:
                raise ValidationError("LIMIT requiere price")
            require_positive(self.price, "price")
            if self.time_in_force is None:
                raise ValidationError("LIMIT requiere time_in_force")
        elif self.order_type is OrderType.MARKET:
            if self.price is not None:
                raise ValidationError("MARKET no admite price")
        else:
            raise ValidationError(f"order_type no soportado: {self.order_type}")


@dataclass(frozen=True, slots=True)
class Order:
    """Orden reconocida por simulador o venue."""

    order_id: str
    client_order_id: str
    instrument_id: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    filled_quantity: Decimal
    price: Decimal | None
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    time_in_force: TimeInForce | None = None

    def __post_init__(self) -> None:
        require_non_empty_str(self.order_id, "order_id")
        require_non_empty_str(self.client_order_id, "client_order_id")
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_positive(self.quantity, "quantity")
        require_non_negative(self.filled_quantity, "filled_quantity")
        if self.filled_quantity > self.quantity:
            raise ValidationError("filled_quantity no puede superar quantity")
        if self.status is OrderStatus.FILLED and self.filled_quantity != self.quantity:
            raise ValidationError("FILLED exige filled_quantity == quantity")
        if self.status in (OrderStatus.PENDING, OrderStatus.OPEN) and self.filled_quantity != 0:
            raise ValidationError(f"{self.status.value} exige filled_quantity == 0")
        require_aware(self.created_at, "created_at")
        require_aware(self.updated_at, "updated_at")
        if self.updated_at < self.created_at:
            raise ValidationError("updated_at debe ser >= created_at")
        if self.order_type is OrderType.LIMIT:
            if self.price is None:
                raise ValidationError("LIMIT requiere price")
            require_positive(self.price, "price")
            if self.time_in_force is None:
                raise ValidationError("LIMIT requiere time_in_force")
        elif self.order_type is OrderType.MARKET:
            if self.price is not None:
                raise ValidationError("MARKET no admite price")
        else:
            raise ValidationError(f"order_type no soportado: {self.order_type}")


@dataclass(frozen=True, slots=True)
class Fee:
    """Costo de transacción."""

    fee_id: str
    fill_id: str
    amount: Decimal
    currency: str
    fee_type: FeeType

    def __post_init__(self) -> None:
        require_non_empty_str(self.fee_id, "fee_id")
        require_non_empty_str(self.fill_id, "fill_id")
        require_non_empty_str(self.currency, "currency")
        require_non_negative(self.amount, "amount")


@dataclass(frozen=True, slots=True)
class Fill:
    """Ejecución parcial o total."""

    fill_id: str
    order_id: str
    instrument_id: str
    price: Decimal
    quantity: Decimal
    fee: Fee
    timestamp: datetime
    liquidity: LiquidityType

    def __post_init__(self) -> None:
        require_non_empty_str(self.fill_id, "fill_id")
        require_non_empty_str(self.order_id, "order_id")
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_positive(self.price, "price")
        require_positive(self.quantity, "quantity")
        require_aware(self.timestamp, "timestamp")
        if self.fee.fill_id != self.fill_id:
            raise ValidationError("fee.fill_id debe coincidir con fill_id")
