"""GenericCsvMdBroker — MD desde CSV (symbol,bid,ask,last) para cualquier plataforma."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from quantlab.brokers.mode import ModeGuard, OperatingMode
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import assert_live_routing_blocked

# Demo in-memory si no hay path (CI / smoke).
_DEFAULT_ROWS: tuple[tuple[str, str, str, str], ...] = (
    ("DEMO/AAA", "100.00", "100.50", "100.25"),
    ("DEMO/BBB", "50.00", "50.25", "50.10"),
)


class GenericCsvMdBroker:
    """Broker MD genérico: snapshots desde CSV o filas demo.

    Columnas requeridas: ``symbol,bid,ask,last`` (header case-insensitive).
    ``submit``/``cancel`` siempre ``assert_live_routing_blocked``.
    """

    def __init__(
        self,
        csv_path: str | Path | None = None,
        mode: OperatingMode = OperatingMode.TESTER,
        *,
        currency: str = "USD",
    ) -> None:
        ModeGuard.validate_boot(mode)
        self._mode = mode
        self._currency = currency
        self._connected = False
        self._csv_path = Path(csv_path) if csv_path else None
        self._snapshots: dict[str, BrokerSnapshot] = {}
        self._instruments: list[BrokerInstrument] = []
        self._load()

    def _load(self) -> None:
        rows: list[tuple[str, Decimal, Decimal, Decimal]] = []
        if self._csv_path is not None and str(self._csv_path).strip():
            path = self._csv_path
            if not path.is_file():
                raise ValidationError(f"CSV MD no encontrado: {path}")
            with path.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                if reader.fieldnames is None:
                    raise ValidationError("CSV MD sin header")
                fields = {f.strip().lower(): f for f in reader.fieldnames if f}
                for required in ("symbol", "bid", "ask", "last"):
                    if required not in fields:
                        raise ValidationError(
                            f"CSV MD requiere columnas symbol,bid,ask,last; falta {required}"
                        )
                for raw in reader:
                    try:
                        symbol = str(raw[fields["symbol"]]).strip()
                        bid = Decimal(str(raw[fields["bid"]]).strip())
                        ask = Decimal(str(raw[fields["ask"]]).strip())
                        last = Decimal(str(raw[fields["last"]]).strip())
                    except (InvalidOperation, KeyError, AttributeError) as exc:
                        raise ValidationError(f"fila CSV MD inválida: {raw!r}") from exc
                    if not symbol:
                        continue
                    rows.append((symbol, bid, ask, last))
        else:
            for symbol, bid_s, ask_s, last_s in _DEFAULT_ROWS:
                rows.append((symbol, Decimal(bid_s), Decimal(ask_s), Decimal(last_s)))

        now = datetime.now(tz=UTC)
        self._snapshots = {
            symbol: BrokerSnapshot(symbol=symbol, bid=bid, ask=ask, last=last, ts=now)
            for symbol, bid, ask, last in rows
        }
        self._instruments = [
            BrokerInstrument(
                symbol=symbol,
                description=f"generic csv {symbol}",
                currency=self._currency,
                status="ACTIVE",
            )
            for symbol in self._snapshots
        ]

    @property
    def venue_id(self) -> str:
        return "generic_csv"

    @property
    def mode(self) -> OperatingMode:
        return self._mode

    def connect(self) -> dict[str, object]:
        self._connected = True
        return {
            "ok": True,
            "venue": self.venue_id,
            "mode": self._mode.value,
            "md_provider": "generic-csv",
            "csv_path": str(self._csv_path) if self._csv_path else None,
        }

    def close(self) -> dict[str, object]:
        self._connected = False
        return {"ok": True, "venue": self.venue_id, "closed": True}

    def health(self) -> dict[str, object]:
        return {
            "ok": self._connected,
            "venue": self.venue_id,
            "mode": self._mode.value,
            "md_provider": "generic-csv",
            "md_only": True,
            "symbols": len(self._snapshots),
            "csv_path": str(self._csv_path) if self._csv_path else None,
        }

    def list_instruments(self) -> list[BrokerInstrument]:
        return list(self._instruments)

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        if symbol not in self._snapshots:
            raise ValidationError(f"símbolo desconocido: {symbol}")
        return self._snapshots[symbol]

    def get_account(self) -> BrokerAccount:
        return BrokerAccount(cash=Decimal("0"), currency=self._currency, equity=None)

    def get_positions(self) -> list[BrokerPosition]:
        return []

    def submit(self, intent: OrderIntent) -> BrokerAck:
        assert_live_routing_blocked()
        raise ValidationError("GenericCsvMdBroker is MD-only; use PaperBroker for PAPER fills")

    def cancel(self, order_id: str) -> BrokerAck:
        assert_live_routing_blocked()
        raise ValidationError("GenericCsvMdBroker is MD-only; use PaperBroker for PAPER cancels")
