"""REST MD skeleton — FakeRestMdBroker in-memory multi-símbolo (Fase 24).

Demuestra registry multiplataforma sin SDK de venue. Un adapter REST real
reemplazaría ``_snapshots`` por HTTP GET; ``submit``/``cancel`` siguen gated.
Ver ``docs/ops/BROKER_PLUGINS.md``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

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

_DEFAULT_SNAPSHOTS: dict[str, tuple[str, str, str]] = {
    "REST/FOO": ("10.00", "10.05", "10.02"),
    "REST/BAR": ("20.00", "20.10", "20.05"),
    "REST/BAZ": ("5.00", "5.02", "5.01"),
}


class FakeRestMdBroker:
    """Skeleton REST MD: dict in-memory configurable (simula respuesta REST).

    Parámetro ``snapshots``: ``{symbol: BrokerSnapshot}`` o se usan demos.
    En producción, un plugin externo haría HTTP aquí; este fake es CI-safe.
    """

    def __init__(
        self,
        mode: OperatingMode = OperatingMode.TESTER,
        *,
        snapshots: dict[str, BrokerSnapshot] | None = None,
        currency: str = "USD",
        base_url: str | None = None,
    ) -> None:
        ModeGuard.validate_boot(mode)
        self._mode = mode
        self._currency = currency
        # Documentado: URL que un adapter real usaría (no se llama en CI).
        self._base_url = base_url or "https://example.invalid/v1/md"
        self._connected = False
        if snapshots is not None:
            self._snapshots = dict(snapshots)
        else:
            now = datetime.now(tz=UTC)
            self._snapshots = {
                sym: BrokerSnapshot(
                    symbol=sym,
                    bid=Decimal(bid),
                    ask=Decimal(ask),
                    last=Decimal(last),
                    ts=now,
                )
                for sym, (bid, ask, last) in _DEFAULT_SNAPSHOTS.items()
            }
        self._instruments = [
            BrokerInstrument(
                symbol=sym,
                description=f"fake rest {sym}",
                currency=self._currency,
                status="ACTIVE",
            )
            for sym in self._snapshots
        ]

    @property
    def venue_id(self) -> str:
        return "generic_rest"

    @property
    def mode(self) -> OperatingMode:
        return self._mode

    def connect(self) -> dict[str, object]:
        self._connected = True
        return {
            "ok": True,
            "venue": self.venue_id,
            "mode": self._mode.value,
            "md_provider": "generic-rest-fake",
            "base_url": self._base_url,
            "note": "skeleton: no HTTP; in-memory snapshots",
        }

    def close(self) -> dict[str, object]:
        self._connected = False
        return {"ok": True, "venue": self.venue_id, "closed": True}

    def health(self) -> dict[str, object]:
        return {
            "ok": self._connected,
            "venue": self.venue_id,
            "mode": self._mode.value,
            "md_provider": "generic-rest-fake",
            "md_only": True,
            "base_url": self._base_url,
            "symbols": len(self._snapshots),
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
        raise ValidationError("FakeRestMdBroker is MD-only; use PaperBroker for PAPER fills")

    def cancel(self, order_id: str) -> BrokerAck:
        assert_live_routing_blocked()
        raise ValidationError("FakeRestMdBroker is MD-only; use PaperBroker for PAPER cancels")
