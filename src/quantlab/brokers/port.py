"""Protocolo BrokerPort — plano multiplataforma (Fase 19)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.types.orders import OrderIntent


@runtime_checkable
class BrokerPort(Protocol):
    """Contrato neutro: MD/cuenta + submit/cancel (implementaciones gated)."""

    @property
    def venue_id(self) -> str: ...

    def connect(self) -> dict[str, object]: ...

    def close(self) -> dict[str, object]: ...

    def health(self) -> dict[str, object]: ...

    def list_instruments(self) -> list[BrokerInstrument]: ...

    def get_snapshot(self, symbol: str) -> BrokerSnapshot: ...

    def get_account(self) -> BrokerAccount: ...

    def get_positions(self) -> list[BrokerPosition]: ...

    def submit(self, intent: OrderIntent) -> BrokerAck: ...

    def cancel(self, order_id: str) -> BrokerAck: ...
