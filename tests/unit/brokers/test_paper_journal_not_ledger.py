"""PaperFillJournal ≠ LocalPaperLedger — separación explícita."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.types import PaperFill
from quantlab.core.exceptions import ValidationError
from quantlab.ledger.local_paper import LocalPaperLedger


def test_journal_append_list_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "paper_fills.jsonl"
    journal = PaperFillJournal(path)
    fill = PaperFill(
        fill_id="f1",
        order_id="o1",
        symbol="BTCUSDT",
        side="buy",
        quantity=Decimal("0.5"),
        price=Decimal("100.25"),
        ts=datetime(2024, 5, 1, 10, 0, tzinfo=UTC),
        source="paper_broker",
    )
    journal.append(fill)
    journal.append(
        PaperFill(
            fill_id="f2",
            order_id="o2",
            symbol="ETHUSDT",
            side="sell",
            quantity=Decimal("1"),
            price=Decimal("50"),
            ts=datetime(2024, 5, 1, 11, 0, tzinfo=UTC),
        )
    )
    fills = journal.list_fills()
    assert len(fills) == 2
    assert fills[0].fill_id == "f1"
    assert fills[0].source == "paper_broker"
    assert fills[1].symbol == "ETHUSDT"
    text = path.read_text(encoding="utf-8")
    assert text.count("\n") == 2
    assert "paper_broker" in text


def test_journal_rejects_wrong_source(tmp_path: Path) -> None:
    journal = PaperFillJournal(tmp_path / "j.jsonl")
    with pytest.raises(ValidationError, match="paper_broker"):
        journal.append(
            PaperFill(
                fill_id="f",
                order_id="o",
                symbol="X",
                side="buy",
                quantity=Decimal("1"),
                price=Decimal("1"),
                ts=datetime(2024, 1, 1, tzinfo=UTC),
                source="local_paper_ledger",
            )
        )


def test_journal_is_not_sqlite_ledger(tmp_path: Path) -> None:
    journal_path = tmp_path / "fills.jsonl"
    ledger_path = tmp_path / "ledger.sqlite"
    journal = PaperFillJournal(journal_path)
    ledger = LocalPaperLedger(ledger_path)

    journal.append(
        PaperFill(
            fill_id="f1",
            order_id="o1",
            symbol="X",
            side="buy",
            quantity=Decimal("1"),
            price=Decimal("10"),
            ts=datetime(2024, 1, 1, tzinfo=UTC),
        )
    )

    assert journal_path.is_file()
    assert ledger_path.is_file()
    assert journal_path != ledger_path
    assert ledger.count() == 0
    assert len(journal.list_fills()) == 1
    # tipos / APIs distintos
    assert not hasattr(journal, "append_simulation")
    assert not hasattr(ledger, "list_fills")
