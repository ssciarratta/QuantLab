"""PaperBroker — fills simulados sobre MD de un BrokerPort subyacente."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.port import BrokerPort
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
    PaperFill,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType
from quantlab.core.types.orders import OrderIntent


def _mid_or_fallback(snapshot: BrokerSnapshot) -> Decimal:
    """Precio de fill: mid si bid/ask válidos; si no last / ask / bid."""
    if snapshot.bid > 0 and snapshot.ask > 0:
        return (snapshot.bid + snapshot.ask) / Decimal("2")
    if snapshot.last > 0:
        return snapshot.last
    if snapshot.ask > 0:
        return snapshot.ask
    if snapshot.bid > 0:
        return snapshot.bid
    raise ValidationError(f"snapshot sin precio usable para {snapshot.symbol}")


class PaperBroker:
    """Ejecución PAPER: nunca envía órdenes al venue subyacente.

    MD/cuenta/posiciones delegan a ``md_port``. Fills locales + journal opcional.
    Aunque ``md_port.venue_id`` sugiera live, este broker no llama submit/cancel
    del venue (fail-closed por diseño de producto).
    """

    def __init__(
        self,
        md_port: BrokerPort,
        journal: PaperFillJournal | None = None,
    ) -> None:
        self._md = md_port
        self._journal = journal
        self._open_orders: dict[str, OrderIntent] = {}
        self._seq = 0

    @property
    def venue_id(self) -> str:
        return "paper"

    def connect(self) -> dict[str, object]:
        return dict(self._md.connect())

    def close(self) -> dict[str, object]:
        return dict(self._md.close())

    def health(self) -> dict[str, object]:
        base = dict(self._md.health())
        base["paper_broker"] = True
        base["md_venue"] = self._md.venue_id
        base["open_orders"] = len(self._open_orders)
        return base

    def list_instruments(self) -> list[BrokerInstrument]:
        return self._md.list_instruments()

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return self._md.get_snapshot(symbol)

    def get_account(self) -> BrokerAccount:
        return self._md.get_account()

    def get_positions(self) -> list[BrokerPosition]:
        return self._md.get_positions()

    def submit(self, intent: OrderIntent) -> BrokerAck:
        if intent.intent_type is IntentType.NO_ACTION:
            return BrokerAck(
                order_id="",
                client_order_id=intent.intent_id,
                status="NO_ACTION",
                message="no-op",
                venue=self.venue_id,
            )
        if intent.intent_type is IntentType.CANCEL_ORDER:
            target = intent.replace_target_id or ""
            return self.cancel(target)
        if intent.intent_type is IntentType.PLACE_ORDER:
            return self._fill_place(intent)
        if intent.intent_type is IntentType.REPLACE_ORDER:
            raise ValidationError("PaperBroker no soporta REPLACE_ORDER en F19")
        raise ValidationError(f"intent_type no soportado: {intent.intent_type}")

    def cancel(self, order_id: str) -> BrokerAck:
        removed = self._open_orders.pop(order_id, None)
        if removed is None:
            return BrokerAck(
                order_id=order_id,
                client_order_id=order_id,
                status="REJECTED",
                message="order not found",
                venue=self.venue_id,
            )
        return BrokerAck(
            order_id=order_id,
            client_order_id=removed.intent_id,
            status="CANCELED",
            message="canceled locally",
            venue=self.venue_id,
        )

    def _fill_place(self, intent: OrderIntent) -> BrokerAck:
        if intent.quantity is None or intent.side is None:
            raise ValidationError("PLACE_ORDER requiere side y quantity")
        snapshot = self._md.get_snapshot(intent.instrument_id)
        price = _mid_or_fallback(snapshot)
        self._seq += 1
        order_id = f"PAPER-{self._seq}-{uuid.uuid4().hex[:8]}"
        fill = PaperFill(
            fill_id=f"PF-{self._seq}-{uuid.uuid4().hex[:8]}",
            order_id=order_id,
            symbol=intent.instrument_id,
            side=intent.side.value,
            quantity=intent.quantity,
            price=price,
            ts=datetime.now(tz=UTC),
            source=PaperFillJournal.SOURCE_TAG,
        )
        if self._journal is not None:
            self._journal.append(fill)
        # Filled inmediato: no queda en open_orders
        return BrokerAck(
            order_id=order_id,
            client_order_id=intent.intent_id,
            status="FILLED",
            message=f"paper fill @ {price}",
            venue=self.venue_id,
        )
