"""PaperBroker — fills simulados sobre MD de un BrokerPort subyacente."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH, PaperBook
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

    MD delega a ``md_port``. Posiciones/cuenta desde ``PaperBook``.
    Fills locales + journal opcional. Nunca llama submit/cancel del MD
    (fail-closed por diseño de producto).
    """

    def __init__(
        self,
        md_port: BrokerPort,
        journal: PaperFillJournal | None = None,
        book: PaperBook | None = None,
        *,
        initial_cash: Decimal | None = None,
        allow_short: bool = False,
        on_book_change: Callable[[PaperBook], None] | None = None,
    ) -> None:
        self._md = md_port
        self._journal = journal
        self._book = book or PaperBook(
            initial_cash=initial_cash if initial_cash is not None else DEFAULT_INITIAL_CASH,
            allow_short=allow_short,
        )
        self._on_book_change = on_book_change
        self._open_orders: dict[str, OrderIntent] = {}
        self._seq = 0

    @property
    def venue_id(self) -> str:
        return "paper"

    @property
    def book(self) -> PaperBook:
        return self._book

    def connect(self) -> dict[str, object]:
        return dict(self._md.connect())

    def close(self) -> dict[str, object]:
        return dict(self._md.close())

    def health(self) -> dict[str, object]:
        base = dict(self._md.health())
        base["paper_broker"] = True
        base["md_venue"] = self._md.venue_id
        base["open_orders"] = len(self._open_orders)
        base["cash"] = str(self._book.cash)
        return base

    def list_instruments(self) -> list[BrokerInstrument]:
        return self._md.list_instruments()

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return self._md.get_snapshot(symbol)

    def get_account(self) -> BrokerAccount:
        marks = self._mark_prices()
        return self._book.get_account(marks)

    def get_positions(self) -> list[BrokerPosition]:
        return self._book.get_positions()

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

    def _mark_prices(self) -> dict[str, Decimal]:
        marks: dict[str, Decimal] = {}
        for pos in self._book.get_positions():
            try:
                snap = self._md.get_snapshot(pos.symbol)
                marks[pos.symbol] = _mid_or_fallback(snap)
            except ValidationError:
                if pos.avg_price is not None:
                    marks[pos.symbol] = pos.avg_price
        return marks

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
        self._book.apply_fill(fill)
        if self._journal is not None:
            self._journal.append(fill)
        if self._on_book_change is not None:
            self._on_book_change(self._book)
        # Filled inmediato: no queda en open_orders
        return BrokerAck(
            order_id=order_id,
            client_order_id=intent.intent_id,
            status="FILLED",
            message=f"paper fill @ {price}",
            venue=self.venue_id,
        )
