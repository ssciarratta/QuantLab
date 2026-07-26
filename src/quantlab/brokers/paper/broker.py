"""PaperBroker — fills simulados sobre MD de un BrokerPort subyacente."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH, PaperBook
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.paper.reconciliation import ReconciliationReport, reconcile_book
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


def apply_paper_slippage(
    price: Decimal,
    side: str,
    slippage_bps: Decimal,
) -> Decimal:
    """Slippage adverso en bps: BUY peor (↑), SELL peor (↓). ``0`` = identidad."""
    if slippage_bps < 0:
        raise ValidationError("slippage_bps no puede ser negativo")
    if slippage_bps >= Decimal("10000"):
        raise ValidationError("slippage_bps debe ser < 10000")
    if slippage_bps == 0:
        return price
    factor = slippage_bps / Decimal("10000")
    side_u = side.strip().upper()
    if side_u == "BUY":
        return price * (Decimal("1") + factor)
    if side_u == "SELL":
        return price * (Decimal("1") - factor)
    raise ValidationError(f"side inválido para slippage: {side!r}")


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
        slippage_bps: Decimal = Decimal("0"),
        on_book_change: Callable[[PaperBook], None] | None = None,
        reconciliation_required: bool = False,
    ) -> None:
        if slippage_bps < 0:
            raise ValidationError("slippage_bps no puede ser negativo")
        if slippage_bps >= Decimal("10000"):
            raise ValidationError("slippage_bps debe ser < 10000")
        self._md = md_port
        self._journal = journal
        self._book = book or PaperBook(
            initial_cash=initial_cash if initial_cash is not None else DEFAULT_INITIAL_CASH,
            allow_short=allow_short,
        )
        self._slippage_bps = Decimal(slippage_bps)
        self._on_book_change = on_book_change
        self._open_orders: dict[str, OrderIntent] = {}
        self._seq = 0
        self._lock = threading.RLock()
        self._reconciliation_required = bool(reconciliation_required)
        self._reconciliation_issue: str | None = (
            "startup reconciliation failed" if reconciliation_required else None
        )

    @property
    def venue_id(self) -> str:
        return "paper"

    @property
    def book(self) -> PaperBook:
        return self._book

    @property
    def slippage_bps(self) -> Decimal:
        return self._slippage_bps

    @property
    def reconciliation_required(self) -> bool:
        with self._lock:
            return self._reconciliation_required

    @property
    def reconciliation_issue(self) -> str | None:
        with self._lock:
            return self._reconciliation_issue

    def mark_reconciliation_required(self, issue: str) -> None:
        with self._lock:
            self._reconciliation_required = True
            self._reconciliation_issue = issue

    def reconcile(self) -> ReconciliationReport:
        """Revalida book/journal bajo el mismo lock usado por submit."""
        with self._lock:
            if self._journal is None:
                raise ValidationError("PaperBroker sin journal durable")
            report = reconcile_book(self._book, self._journal)
            self._reconciliation_required = not report.ok
            self._reconciliation_issue = None if report.ok else "; ".join(report.issues)
            return report

    def inspect_reconciliation(
        self, check: Callable[[], ReconciliationReport]
    ) -> ReconciliationReport:
        """Serializa un check durable externo con submit y actualiza el gate."""
        with self._lock:
            report = check()
            self._reconciliation_required = not report.ok
            self._reconciliation_issue = None if report.ok else "; ".join(report.issues)
            return report

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
        base["reconciliation_required"] = self.reconciliation_required
        return base

    def list_instruments(self) -> list[BrokerInstrument]:
        return self._md.list_instruments()

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return self._md.get_snapshot(symbol)

    def get_account(self) -> BrokerAccount:
        with self._lock:
            marks = self.mark_prices()
            return self._book.get_account(marks)

    def get_positions(self) -> list[BrokerPosition]:
        with self._lock:
            return self._book.get_positions()

    def mark_prices(self) -> dict[str, Decimal]:
        """Marks MTM por símbolo abierto (mid/last MD; fallback avg)."""
        return self._mark_prices()

    def get_pnl(self) -> dict[str, Decimal]:
        """PnL summary realized/unrealized/equity/cash con marks MD (F67)."""
        return self._book.get_pnl(self.mark_prices())

    def submit(self, intent: OrderIntent) -> BrokerAck:
        with self._lock:
            if self._reconciliation_required:
                issue = self._reconciliation_issue or "drift detectado"
                raise ValidationError(
                    f"paper submit bloqueado: reconciliation_required ({issue}); "
                    "ejecutar CLI --check/--rebuild y recargar"
                )
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
        with self._lock:
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
        mid = _mid_or_fallback(snapshot)
        price = apply_paper_slippage(mid, intent.side.value, self._slippage_bps)
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
        # Preview completo antes del commit: jamás mutar live book si el fill no aplica.
        preview = PaperBook.from_dict(self._book.to_dict())
        preview.apply_fill(fill)

        # Commit durable en orden journal -> memoria -> proyección atómica.
        if self._journal is not None:
            try:
                self._journal.append(fill)
            except Exception as exc:
                self._reconciliation_required = True
                self._reconciliation_issue = f"journal append incierto: {exc}"
                raise ValidationError(
                    "paper submit bloqueado tras falla de journal; reconciliación requerida"
                ) from exc
        try:
            self._book.apply_fill(fill)
        except Exception as exc:
            self._reconciliation_required = True
            self._reconciliation_issue = f"journal ahead tras apply: {exc}"
            raise ValidationError(
                "journal committed pero book apply falló; reconciliación requerida"
            ) from exc
        if self._on_book_change is not None:
            try:
                self._on_book_change(self._book)
            except Exception as exc:
                self._reconciliation_required = True
                self._reconciliation_issue = f"book persist falló post-journal: {exc}"
                raise ValidationError(
                    "journal committed pero book persist falló; reconciliación requerida"
                ) from exc
        # Filled inmediato: no queda en open_orders
        return BrokerAck(
            order_id=order_id,
            client_order_id=intent.intent_id,
            status="FILLED",
            message=f"paper fill @ {price}",
            venue=self.venue_id,
        )
