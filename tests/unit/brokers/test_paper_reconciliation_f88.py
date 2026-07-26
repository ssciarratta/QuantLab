"""F88: journal paper autoritativo, reconciliación y rebuild offline."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.paper.reconciliation import rebuild_book, reconcile_book
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
    PaperFill,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType
from quantlab.core.types.orders import OrderIntent
from quantlab.workbench.api import WorkbenchState, handle_get_paper_reconciliation
from quantlab.workbench.session import WorkbenchSession

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from reconcile_paper_session import check_session, rebuild_session  # noqa: E402


def _fill(
    fill_id: str = "fill-1",
    order_id: str = "order-1",
    *,
    side: str = "buy",
) -> PaperFill:
    return PaperFill(
        fill_id=fill_id,
        order_id=order_id,
        symbol="TEST",
        side=side,
        quantity=Decimal("2"),
        price=Decimal("11.25"),
        ts=datetime(2026, 7, 26, 12, tzinfo=UTC),
        source="paper_broker",
    )


class _Md:
    @property
    def venue_id(self) -> str:
        return "md"

    def connect(self) -> dict[str, object]:
        return {"ok": True}

    def close(self) -> dict[str, object]:
        return {"ok": True}

    def health(self) -> dict[str, object]:
        return {"ok": True}

    def list_instruments(self) -> list[BrokerInstrument]:
        return []

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return BrokerSnapshot(
            symbol=symbol,
            bid=Decimal("10"),
            ask=Decimal("12"),
            last=Decimal("11"),
            ts=datetime.now(tz=UTC),
        )

    def get_account(self) -> BrokerAccount:
        return BrokerAccount(Decimal("0"), "USD")

    def get_positions(self) -> list[BrokerPosition]:
        return []

    def submit(self, intent: OrderIntent) -> object:
        raise AssertionError("venue submit no debe invocarse")

    def cancel(self, order_id: str) -> object:
        raise AssertionError("venue cancel no debe invocarse")


def _intent() -> OrderIntent:
    return OrderIntent(
        intent_id="intent-1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="TEST",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        order_type=OrderType.MARKET,
    )


def test_journal_roundtrip_checkpoint_and_exact_replay(tmp_path: Path) -> None:
    journal = PaperFillJournal(tmp_path / "journal.jsonl")
    journal.append(_fill())
    fills = journal.read_strict()
    checkpoint = journal.checkpoint()
    book = rebuild_book(Decimal("1000"), "USD", False, fills)

    assert fills == [_fill()]
    assert checkpoint.record_count == 1
    assert checkpoint.last_fill_id == "fill-1"
    assert len(checkpoint.sha256) == 64
    assert reconcile_book(book, journal).ok is True


def test_append_rejects_duplicate_fill_id(tmp_path: Path) -> None:
    journal = PaperFillJournal(tmp_path / "journal.jsonl")
    journal.append(_fill())
    with pytest.raises(ValidationError, match="duplicate fill_id"):
        journal.append(_fill(order_id="order-2"))
    assert journal.checkpoint().record_count == 1


@pytest.mark.parametrize(
    "body,match",
    [
        ('{"fill_id":', "truncado"),
        ("\n", "línea vacía"),
        (
            json.dumps(
                {
                    "fill_id": "f",
                    "order_id": "o",
                    "symbol": "X",
                    "side": "buy",
                    "quantity": "NaN",
                    "price": "1",
                    "ts": "2026-01-01T00:00:00+00:00",
                    "source": "paper_broker",
                }
            )
            + "\n",
            "finito",
        ),
    ],
)
def test_strict_reader_rejects_malformed_records(
    tmp_path: Path, body: str, match: str
) -> None:
    path = tmp_path / "journal.jsonl"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(ValidationError, match=match):
        PaperFillJournal(path).read_strict()


def test_strict_reader_detects_duplicate_order_id(tmp_path: Path) -> None:
    journal = PaperFillJournal(tmp_path / "journal.jsonl")
    journal.append(_fill())
    payload = json.loads(journal.path.read_text(encoding="utf-8"))
    payload["fill_id"] = "fill-2"
    with journal.path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    with pytest.raises(ValidationError, match="duplicate order_id"):
        journal.read_strict()


def test_session_book_v2_and_atomic_failure_preserves_old_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "atomic")
    raw_before = session.book_path.read_bytes()

    def _fail(_path: Path, _text: str) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr("quantlab.workbench.session.atomic_write_text", _fail)
    with pytest.raises(OSError, match="injected"):
        session.save_book(PaperBook(initial_cash=Decimal("7")))
    assert session.book_path.read_bytes() == raw_before
    assert json.loads(raw_before)["schema_version"] == 2


def test_legacy_flat_book_migrates_only_when_consistent(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "legacy")
    legacy = PaperBook(initial_cash=Decimal("1234")).to_dict()
    session.book_path.write_text(json.dumps(legacy), encoding="utf-8")
    state = WorkbenchState(session=session, session_parent=tmp_path)

    state.ensure_session()

    assert state.paper_reconciliation is not None
    assert state.paper_reconciliation.ok is True
    assert "legacy_book_migrated" in state.paper_reconciliation.issues
    assert json.loads(session.book_path.read_text(encoding="utf-8"))["schema_version"] == 2


def test_journal_ahead_boot_blocks_submit_until_cli_rebuild(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "ahead")
    PaperFillJournal(session.journal_path).append(_fill())
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()

    assert state.paper_reconciliation is not None
    assert state.paper_reconciliation.status == "rebuild_required"
    assert "journal_ahead" in state.paper_reconciliation.issues
    broker = PaperBroker(
        _Md(),  # type: ignore[arg-type]
        journal=state.ensure_journal(),
        book=state.ensure_book(),
        reconciliation_required=True,
    )
    with pytest.raises(ValidationError, match="reconciliation_required"):
        broker.submit(_intent())


def test_book_mismatch_and_book_ahead_checkpoint_fail_closed(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "mismatch")
    payload = json.loads(session.book_path.read_text(encoding="utf-8"))
    payload["book"]["cash"] = "999"
    payload["journal_checkpoint"]["record_count"] = 4
    payload["journal_checkpoint"]["last_fill_id"] = "future"
    session.book_path.write_text(json.dumps(payload), encoding="utf-8")

    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()

    assert state.paper_reconciliation is not None
    assert state.paper_reconciliation.ok is False
    assert "book_ahead" in state.paper_reconciliation.issues
    assert "book_mismatch" in state.paper_reconciliation.issues


def test_post_journal_book_persist_failure_blocks_followup_submit(tmp_path: Path) -> None:
    journal = PaperFillJournal(tmp_path / "journal.jsonl")

    def _fail(_book: PaperBook) -> None:
        raise OSError("disk full")

    broker = PaperBroker(
        _Md(),  # type: ignore[arg-type]
        journal=journal,
        on_book_change=_fail,
    )
    with pytest.raises(ValidationError, match="persist falló"):
        broker.submit(_intent())
    assert journal.checkpoint().record_count == 1
    assert broker.get_positions()[0].quantity == Decimal("1")
    with pytest.raises(ValidationError, match="reconciliation_required"):
        broker.submit(_intent())
    assert journal.checkpoint().record_count == 1


def test_cli_rebuild_creates_backup_and_never_mutates_journal(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "cli")
    journal = PaperFillJournal(session.journal_path)
    journal.append(_fill())
    journal_before = session.journal_path.read_bytes()

    assert check_session(session.root).status == "rebuild_required"
    report, backup = rebuild_session(session.root)

    assert report.ok is True
    assert backup is not None and backup.name.startswith("book.json.bak-")
    assert backup.read_bytes() != session.book_path.read_bytes()
    assert session.journal_path.read_bytes() == journal_before
    assert check_session(session.root).ok is True


def test_reconciliation_http_handler_is_read_only(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    before = session.journal_path.read_bytes()

    payload = handle_get_paper_reconciliation(state)

    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert session.journal_path.read_bytes() == before


def test_http_check_does_not_migrate_externally_downgraded_legacy_book(
    tmp_path: Path,
) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "http-legacy")
    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()
    legacy_text = json.dumps(PaperBook().to_dict())
    session.book_path.write_text(legacy_text, encoding="utf-8")

    payload = handle_get_paper_reconciliation(state)

    assert payload["ok"] is False
    assert "legacy_format" in payload["issues"]
    assert session.book_path.read_text(encoding="utf-8") == legacy_text


def test_missing_book_with_nonempty_journal_is_not_silently_recreated(
    tmp_path: Path,
) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "missing")
    PaperFillJournal(session.journal_path).append(_fill())
    session.book_path.unlink()

    reopened = WorkbenchSession.create_or_load(tmp_path, "missing")
    state = WorkbenchState(session=reopened, session_parent=tmp_path)
    state.ensure_session()

    assert reopened.book_path.exists() is False
    assert state.paper_reconciliation is not None
    assert "book_missing" in state.paper_reconciliation.issues


def test_book_zero_position_is_corruption_not_equal_state(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "zero-position")
    payload = json.loads(session.book_path.read_text(encoding="utf-8"))
    payload["book"]["positions"]["GHOST"] = {"quantity": "0", "avg_price": "1"}
    session.book_path.write_text(json.dumps(payload), encoding="utf-8")

    state = WorkbenchState(session=session, session_parent=tmp_path)
    state.ensure_session()

    assert state.paper_reconciliation is not None
    assert state.paper_reconciliation.status == "book_corrupt"
