"""Paper PnL summary — realized/unrealized/equity/cash (F67).

Fuente: ``PaperBook.get_pnl`` + marks del PaperBroker (o avg fallback).
Sin flip LIVE · sin place_order venue.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.execution.live_gate import LIVE_BLOCKED


def _as_str_decimal(value: Decimal) -> str:
    return str(value)


def summarize_paper_pnl(
    book: PaperBook,
    *,
    mark_prices: dict[str, Decimal] | None = None,
    marks_source: str = "avg",
) -> dict[str, Any]:
    """Payload PnL Decimal-safe (strings) desde book + marks."""
    marks = dict(mark_prices or {})
    pnl = book.get_pnl(marks if marks else None)
    marks_out = {sym: _as_str_decimal(px) for sym, px in sorted(marks.items())}
    return {
        "ok": True,
        "kind": "pnl",
        "cash": _as_str_decimal(pnl["cash"]),
        "equity": _as_str_decimal(pnl["equity"]),
        "realized": _as_str_decimal(pnl["realized"]),
        "unrealized": _as_str_decimal(pnl["unrealized"]),
        "initial_cash": _as_str_decimal(pnl["initial_cash"]),
        "currency": book.currency,
        "marks": marks_out,
        "marks_source": marks_source,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def pnl_from_broker(broker: PaperBroker) -> dict[str, Any]:
    """PnL con marks mid/last del MD subyacente del PaperBroker."""
    marks = broker.mark_prices()
    return summarize_paper_pnl(broker.book, mark_prices=marks, marks_source="broker")


def pnl_from_book(book: PaperBook) -> dict[str, Any]:
    """PnL sin broker: marks = avg_price de cada posición."""
    return summarize_paper_pnl(book, mark_prices=None, marks_source="avg")
