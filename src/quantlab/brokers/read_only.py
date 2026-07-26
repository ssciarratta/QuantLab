"""Read-only enforcement wrapper for external broker plugins."""

from __future__ import annotations

from quantlab.brokers.port import BrokerPort
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


class ReadOnlyBrokerPort:
    """Delegate lifecycle/read methods and fail closed for execution methods."""

    __slots__ = ("__broker",)

    def __init__(self, broker: BrokerPort) -> None:
        self.__broker = broker

    @property
    def venue_id(self) -> str:
        return self.__broker.venue_id

    def connect(self) -> dict[str, object]:
        return self.__broker.connect()

    def close(self) -> dict[str, object]:
        return self.__broker.close()

    def health(self) -> dict[str, object]:
        return self.__broker.health()

    def list_instruments(self) -> list[BrokerInstrument]:
        return self.__broker.list_instruments()

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return self.__broker.get_snapshot(symbol)

    def get_account(self) -> BrokerAccount:
        return self.__broker.get_account()

    def get_positions(self) -> list[BrokerPosition]:
        return self.__broker.get_positions()

    def submit(self, intent: OrderIntent) -> BrokerAck:
        del intent
        assert_live_routing_blocked()
        raise ValidationError("external broker plugins are read-only")

    def cancel(self, order_id: str) -> BrokerAck:
        del order_id
        assert_live_routing_blocked()
        raise ValidationError("external broker plugins are read-only")
