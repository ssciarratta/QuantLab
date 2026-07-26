"""Tests WorkbenchSession durable (persistencia root)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.types import PaperFill
from quantlab.core.exceptions import ValidationError
from quantlab.workbench.session import WorkbenchSession, validate_session_id


def test_create_or_load_layout(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "s1", initial_cash=Decimal("25000"))
    assert session.session_id == "s1"
    assert session.root == (tmp_path / "s1").resolve()
    assert session.journal_path.is_file()
    assert session.book_path.is_file()
    assert session.meta_path.is_file()
    assert session.experiments_dir.is_dir()
    assert session.exports_dir.is_dir()
    assert session.chat_audit_path.is_file()
    book = session.load_book()
    assert book.cash == Decimal("25000")
    meta = session.load_meta()
    assert meta["session_id"] == "s1"
    assert meta["initial_cash"] == "25000"


def test_session_id_path_traversal_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="session_id"):
        WorkbenchSession.create_or_load(tmp_path, "../escape-audit")
    with pytest.raises(ValidationError, match="session_id"):
        WorkbenchSession.create_or_load(tmp_path, "a/b")
    with pytest.raises(ValidationError, match="session_id"):
        validate_session_id("..")
    assert validate_session_id("ok-session_1") == "ok-session_1"


def test_session_book_persist_reload(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "persist")
    book = session.load_book()
    fill = PaperFill(
        fill_id="f",
        order_id="o",
        symbol="X",
        side="buy",
        quantity=Decimal("1"),
        price=Decimal("10"),
        ts=datetime(2024, 1, 1, tzinfo=UTC),
    )
    PaperFillJournal(session.journal_path).append(fill)
    book.apply_fill(fill)
    session.save_book(book)

    again = WorkbenchSession.create_or_load(tmp_path, "persist")
    restored = again.load_book()
    assert restored.cash == Decimal("100000") - Decimal("10")
    assert restored.get_positions()[0].symbol == "X"


def test_to_dict_includes_paths(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "meta-paths")
    payload = session.to_dict()
    assert payload["session_id"] == "meta-paths"
    assert "journal" in payload
    assert Path(payload["root"]).exists()
