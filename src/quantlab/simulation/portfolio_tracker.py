"""Tracker mutable interno → snapshots inmutables de portfolio."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import OrderSide
from quantlab.core.types.portfolio import Balance, PortfolioState, Position

# Cantidad residual mínima para promedio ponderado (evita división degenerada)
_MIN_QTY = Decimal("1e-12")


def _require_finite(value: Decimal, field: str) -> None:
    if value.is_nan() or value.is_infinite():
        raise ValidationError(f"{field} no puede ser NaN ni Infinity")


@dataclass
class _OpenPosition:
    quantity: Decimal = Decimal("0")
    avg_entry: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")


@dataclass
class PortfolioTracker:
    """Contabilidad cash + posición por instrumento (MVP Fase 4)."""

    cash_asset: str
    cash: Decimal
    fee_rate: Decimal = Decimal("0")
    positions: dict[str, _OpenPosition] = field(default_factory=dict)
    total_realized: Decimal = Decimal("0")

    def can_afford(
        self,
        side: OrderSide,
        instrument_id: str,
        quantity: Decimal,
        price: Decimal,
        *,
        fee: Decimal | None = None,
    ) -> bool:
        notional = quantity * price
        fee_amt = fee if fee is not None else notional * self.fee_rate
        if side is OrderSide.BUY:
            return self.cash >= notional + fee_amt
        pos = self.positions.get(instrument_id)
        return pos is not None and pos.quantity >= quantity

    def apply_fill(
        self,
        *,
        instrument_id: str,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal | None = None,
    ) -> Decimal:
        """Aplica fill; retorna fee cobrada. Lanza ValueError si no hay fondos/stock."""
        _require_finite(quantity, "quantity")
        _require_finite(price, "price")
        if quantity <= 0:
            raise ValueError("quantity must be > 0")
        if price <= 0:
            raise ValueError("price must be > 0")
        notional = quantity * price
        fee_amt = (
            fee if fee is not None else (notional * self.fee_rate).quantize(Decimal("0.00000001"))
        )
        _require_finite(fee_amt, "fee")
        pos = self.positions.setdefault(instrument_id, _OpenPosition())

        if side is OrderSide.BUY:
            cost = notional + fee_amt
            if self.cash < cost:
                raise ValueError("insufficient_cash")
            new_qty = pos.quantity + quantity
            if new_qty <= _MIN_QTY:
                pos.avg_entry = price
                pos.quantity = new_qty if new_qty > 0 else Decimal("0")
            elif pos.quantity > 0:
                pos.avg_entry = (pos.avg_entry * pos.quantity + price * quantity) / new_qty
                pos.quantity = new_qty
            else:
                pos.avg_entry = price
                pos.quantity = quantity
            self.cash -= cost
        else:
            if pos.quantity < quantity:
                raise ValueError("insufficient_position")
            proceeds = notional - fee_amt
            realized = (price - pos.avg_entry) * quantity
            pos.quantity -= quantity
            pos.realized_pnl += realized
            self.total_realized += realized
            self.cash += proceeds
            if pos.quantity <= _MIN_QTY:
                pos.quantity = Decimal("0")
                pos.avg_entry = Decimal("0")
        return fee_amt

    def mark_equity(self, marks: dict[str, Decimal], timestamp: datetime) -> PortfolioState:
        for iid, mark in marks.items():
            _require_finite(mark, f"mark[{iid}]")
        unrealized = Decimal("0")
        positions: list[Position] = []
        for iid, pos in sorted(self.positions.items()):
            if pos.quantity == 0:
                continue
            mark = marks.get(iid, pos.avg_entry)
            _require_finite(mark, f"mark[{iid}]")
            u = (mark - pos.avg_entry) * pos.quantity
            _require_finite(u, "unrealized_pnl")
            unrealized += u
            positions.append(
                Position(
                    instrument_id=iid,
                    quantity=pos.quantity,
                    avg_entry_price=pos.avg_entry,
                    unrealized_pnl=u,
                    realized_pnl=pos.realized_pnl,
                    updated_at=timestamp,
                )
            )
        equity = self.cash + sum(
            (marks.get(p.instrument_id, p.avg_entry_price) * p.quantity for p in positions),
            Decimal("0"),
        )
        _require_finite(equity, "total_equity")
        _require_finite(self.cash, "cash")
        return PortfolioState(
            timestamp=timestamp,
            positions=tuple(positions),
            balances=(
                Balance(
                    asset=self.cash_asset,
                    available=self.cash,
                    locked=Decimal("0"),
                    total=self.cash,
                    updated_at=timestamp,
                ),
            ),
            total_equity=equity,
            total_realized_pnl=self.total_realized,
            total_unrealized_pnl=unrealized,
        )
