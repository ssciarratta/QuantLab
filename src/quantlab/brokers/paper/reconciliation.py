"""Reconciliación del journal autoritativo y la proyección ``PaperBook``."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.types import PaperFill
from quantlab.core.exceptions import ValidationError

if TYPE_CHECKING:
    from quantlab.brokers.paper.journal import PaperFillJournal


@dataclass(frozen=True, slots=True)
class JournalCheckpoint:
    """Identidad verificable de un prefijo completo del journal."""

    record_count: int
    last_fill_id: str | None
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JournalCheckpoint:
        if not isinstance(data, dict):
            raise ValidationError("journal_checkpoint debe ser objeto")
        try:
            record_count = int(data["record_count"])
            last_fill_raw = data.get("last_fill_id")
            last_fill_id = None if last_fill_raw is None else str(last_fill_raw)
            sha256 = str(data["sha256"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError(f"journal_checkpoint inválido: {exc}") from exc
        if record_count < 0:
            raise ValidationError("journal_checkpoint.record_count no puede ser negativo")
        if record_count == 0 and last_fill_id is not None:
            raise ValidationError("checkpoint vacío no puede tener last_fill_id")
        if record_count > 0 and not last_fill_id:
            raise ValidationError("checkpoint no vacío requiere last_fill_id")
        if len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256.lower()):
            raise ValidationError("journal_checkpoint.sha256 inválido")
        return cls(record_count, last_fill_id, sha256.lower())


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Resultado serializable de comparar journal y proyección."""

    ok: bool
    status: str
    record_count: int
    issues: tuple[str, ...]
    expected_book: dict[str, Any] | None
    persisted_book: dict[str, Any]
    checkpoint: JournalCheckpoint | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["issues"] = list(self.issues)
        return payload


def _state(book: PaperBook) -> tuple[Any, ...]:
    """Estado económico exacto, independiente del orden de serialización."""
    positions = tuple(
        (position.symbol, position.quantity, position.avg_price)
        for position in book.get_positions()
    )
    return (
        book.initial_cash,
        book.cash,
        book.currency,
        book.allow_short,
        positions,
    )


def rebuild_book(
    initial_cash: Decimal,
    currency: str,
    allow_short: bool,
    fills: Iterable[PaperFill],
) -> PaperBook:
    """Reconstruye una proyección exclusivamente mediante replay ordenado."""
    book = PaperBook(
        initial_cash=Decimal(initial_cash),
        currency=currency,
        allow_short=allow_short,
    )
    for index, fill in enumerate(fills, start=1):
        try:
            book.apply_fill(fill)
        except ValidationError as exc:
            raise ValidationError(f"journal replay falló en registro {index}: {exc}") from exc
    return book


def reconcile_book(book: PaperBook, journal: PaperFillJournal) -> ReconciliationReport:
    """Compara estado Decimal exacto; corrupción se informa fail-closed."""
    try:
        fills = journal.read_strict()
        checkpoint = journal.checkpoint()
        expected = rebuild_book(
            book.initial_cash,
            book.currency,
            book.allow_short,
            fills,
        )
    except (OSError, UnicodeError, ValidationError) as exc:
        return ReconciliationReport(
            ok=False,
            status="journal_corrupt",
            record_count=0,
            issues=(str(exc),),
            expected_book=None,
            persisted_book=book.to_dict(),
            checkpoint=None,
        )

    if _state(expected) == _state(book):
        return ReconciliationReport(
            ok=True,
            status="ok",
            record_count=len(fills),
            issues=(),
            expected_book=expected.to_dict(),
            persisted_book=book.to_dict(),
            checkpoint=checkpoint,
        )
    return ReconciliationReport(
        ok=False,
        status="rebuild_required",
        record_count=len(fills),
        issues=("book_mismatch",),
        expected_book=expected.to_dict(),
        persisted_book=book.to_dict(),
        checkpoint=checkpoint,
    )
