"""Risk fail-closed para paper submit del workbench."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantlab.brokers.types import BrokerSnapshot
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType
from quantlab.core.types.orders import OrderIntent

DEFAULT_MAX_QTY = Decimal("1000")
DEFAULT_MAX_NOTIONAL = Decimal("500000")


@dataclass(frozen=True, slots=True)
class PaperRiskLimits:
    """Límites paper: max qty / notional / símbolos permitidos."""

    max_qty: Decimal = DEFAULT_MAX_QTY
    max_notional: Decimal = DEFAULT_MAX_NOTIONAL
    allowed_symbols: frozenset[str] | None = None

    def check_intent(self, intent: OrderIntent, snapshot: BrokerSnapshot) -> None:
        """Raise ``ValidationError`` si el intent viola límites."""
        if intent.intent_type is not IntentType.PLACE_ORDER:
            return
        symbol = intent.instrument_id.strip()
        if self.allowed_symbols is not None and symbol not in self.allowed_symbols:
            raise ValidationError(
                f"símbolo no permitido por risk paper: {symbol!r} "
                f"(allowed={sorted(self.allowed_symbols)})"
            )
        if intent.quantity is None:
            raise ValidationError("PLACE_ORDER requiere quantity (risk)")
        qty = Decimal(intent.quantity)
        if qty <= 0:
            raise ValidationError("quantity debe ser > 0 (risk)")
        if qty > self.max_qty:
            raise ValidationError(f"quantity {qty} excede max_qty={self.max_qty}")
        mark = _mark_from_snapshot(snapshot)
        notional = qty * mark
        if notional > self.max_notional:
            raise ValidationError(
                f"notional {notional} excede max_notional={self.max_notional} "
                f"(qty={qty} × mark={mark})"
            )


def _mark_from_snapshot(snapshot: BrokerSnapshot) -> Decimal:
    if snapshot.bid > 0 and snapshot.ask > 0:
        return (snapshot.bid + snapshot.ask) / Decimal("2")
    if snapshot.last > 0:
        return snapshot.last
    if snapshot.ask > 0:
        return snapshot.ask
    if snapshot.bid > 0:
        return snapshot.bid
    raise ValidationError(f"snapshot sin precio usable para risk: {snapshot.symbol}")
