"""Market Replay 5B — stream ordenado de trades y libros."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import EventType
from quantlab.core.types.market import MarketEvent, OrderBookSnapshot, Trade


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    """Evento de replay tipado para el motor 5B."""

    timestamp: datetime
    event_type: EventType
    trade: Trade | None = None
    book: OrderBookSnapshot | None = None


class MarketReplay:
    """Reproduce trades y snapshots de libro en orden temporal estricto."""

    def __init__(
        self,
        *,
        trades: Sequence[Trade] = (),
        books: Sequence[OrderBookSnapshot] = (),
    ) -> None:
        self._events = self._build(trades, books)

    @staticmethod
    def _build(
        trades: Sequence[Trade], books: Sequence[OrderBookSnapshot]
    ) -> tuple[ReplayEvent, ...]:
        raw: list[ReplayEvent] = []
        for t in trades:
            raw.append(ReplayEvent(timestamp=t.timestamp, event_type=EventType.TRADE, trade=t))
        for b in books:
            raw.append(
                ReplayEvent(
                    timestamp=b.timestamp,
                    event_type=EventType.ORDER_BOOK_SNAPSHOT,
                    book=b,
                )
            )
        raw.sort(key=lambda e: (e.timestamp, e.event_type.value))
        prev: datetime | None = None
        for e in raw:
            if prev is not None and e.timestamp < prev:
                raise ValidationError("replay no monótono")
            prev = e.timestamp
        return tuple(raw)

    def __iter__(self) -> Iterator[ReplayEvent]:
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def as_market_events(self) -> tuple[MarketEvent, ...]:
        out: list[MarketEvent] = []
        for i, e in enumerate(self._events):
            if e.trade is not None:
                out.append(
                    MarketEvent(
                        event_id=f"replay-trade-{i:06d}",
                        event_type=EventType.TRADE,
                        timestamp=e.timestamp,
                        instrument_id=e.trade.instrument_id,
                        payload={
                            "price": str(e.trade.price),
                            "quantity": str(e.trade.quantity),
                            "side": e.trade.side.value,
                            "trade_id": e.trade.trade_id,
                        },
                    )
                )
            elif e.book is not None:
                out.append(
                    MarketEvent(
                        event_id=f"replay-book-{i:06d}",
                        event_type=EventType.ORDER_BOOK_SNAPSHOT,
                        timestamp=e.timestamp,
                        instrument_id=e.book.instrument_id,
                        payload={
                            "sequence_id": e.book.sequence_id,
                            "best_bid": str(e.book.bids[0].price) if e.book.bids else None,
                            "best_ask": str(e.book.asks[0].price) if e.book.asks else None,
                        },
                    )
                )
        return tuple(out)
