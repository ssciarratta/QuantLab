"""Tests PaperBook — fills → cash/posiciones/equity + persistencia."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.types import PaperFill
from quantlab.core.exceptions import ValidationError


def _fill(
    *,
    side: str,
    qty: str,
    price: str,
    symbol: str = "TEST",
) -> PaperFill:
    return PaperFill(
        fill_id="f1",
        order_id="o1",
        symbol=symbol,
        side=side,
        quantity=Decimal(qty),
        price=Decimal(price),
        ts=datetime(2024, 1, 1, tzinfo=UTC),
    )


def test_buy_reduces_cash_and_opens_position() -> None:
    book = PaperBook(initial_cash=Decimal("1000"))
    book.apply_fill(_fill(side="buy", qty="2", price="100"))
    assert book.cash == Decimal("800")
    pos = book.get_positions()
    assert len(pos) == 1
    assert pos[0].symbol == "TEST"
    assert pos[0].quantity == Decimal("2")
    assert pos[0].avg_price == Decimal("100")


def test_avg_price_weighted_on_buy() -> None:
    book = PaperBook(initial_cash=Decimal("10000"))
    book.apply_fill(_fill(side="buy", qty="2", price="100"))
    book.apply_fill(_fill(side="buy", qty="2", price="200"))
    pos = book.get_positions()[0]
    assert pos.quantity == Decimal("4")
    assert pos.avg_price == Decimal("150")


def test_sell_increases_cash_and_reduces_qty() -> None:
    book = PaperBook(initial_cash=Decimal("1000"))
    book.apply_fill(_fill(side="buy", qty="5", price="10"))
    book.apply_fill(_fill(side="sell", qty="2", price="12"))
    assert book.cash == Decimal("1000") - Decimal("50") + Decimal("24")
    pos = book.get_positions()[0]
    assert pos.quantity == Decimal("3")
    assert pos.avg_price == Decimal("10")


def test_reject_short_by_default() -> None:
    book = PaperBook(initial_cash=Decimal("1000"))
    book.apply_fill(_fill(side="buy", qty="1", price="10"))
    with pytest.raises(ValidationError, match="short no permitido"):
        book.apply_fill(_fill(side="sell", qty="2", price="10"))


def test_allow_short_when_flag() -> None:
    book = PaperBook(initial_cash=Decimal("1000"), allow_short=True)
    book.apply_fill(_fill(side="sell", qty="2", price="50"))
    assert book.cash == Decimal("1100")
    pos = book.get_positions()[0]
    assert pos.quantity == Decimal("-2")


def test_reject_insufficient_cash() -> None:
    book = PaperBook(initial_cash=Decimal("50"))
    with pytest.raises(ValidationError, match="cash insuficiente"):
        book.apply_fill(_fill(side="buy", qty="1", price="100"))


def test_equity_mtm() -> None:
    book = PaperBook(initial_cash=Decimal("1000"))
    book.apply_fill(_fill(side="buy", qty="2", price="100"))
    acct = book.get_account(mark_prices={"TEST": Decimal("110")})
    assert acct.cash == Decimal("800")
    assert acct.equity == Decimal("800") + Decimal("220")


def test_to_dict_from_dict_roundtrip() -> None:
    book = PaperBook(initial_cash=Decimal("5000"), currency="USDT")
    book.apply_fill(_fill(side="buy", qty="1", price="100", symbol="AAA"))
    payload = book.to_dict()
    restored = PaperBook.from_dict(payload)
    assert restored.cash == book.cash
    assert restored.initial_cash == book.initial_cash
    assert restored.get_positions()[0].quantity == Decimal("1")
    assert restored.get_account().equity == book.get_account().equity


def test_reject_negative_cash_on_init_and_from_dict() -> None:
    with pytest.raises(ValidationError, match="cash no puede ser negativo"):
        PaperBook(initial_cash=Decimal("100"), cash=Decimal("-1"))
    with pytest.raises(ValidationError, match="cash no puede ser negativo"):
        PaperBook.from_dict({"initial_cash": "100", "cash": "-50", "positions": {}})


def test_reject_short_positions_when_allow_short_false() -> None:
    with pytest.raises(ValidationError, match="short no permitido"):
        PaperBook(
            initial_cash=Decimal("1000"),
            allow_short=False,
            positions={"X": (Decimal("-1"), Decimal("10"))},
        )
