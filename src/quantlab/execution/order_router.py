"""OrderRouter — NullRouter default (DEC-014). Sin routing LIVE."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from quantlab.execution.live_gate import assert_live_routing_blocked

if TYPE_CHECKING:
    from quantlab.data.exchanges.a3.models import A3OrderAckDTO
    from quantlab.data.exchanges.a3.protocols import A3Backend


@runtime_checkable
class OrderRouter(Protocol):
    """Contrato de envío de órdenes (fail-closed por defecto)."""

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        size: str,
        order_type: str,
        price: str | None,
        client_order_id: str,
    ) -> A3OrderAckDTO: ...

    def cancel_order(self, order_id: str) -> A3OrderAckDTO: ...


class NullRouter:
    """Router por defecto: nunca envía; siempre dispara live_gate."""

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        size: str,
        order_type: str,
        price: str | None,
        client_order_id: str,
    ) -> Any:
        _ = (symbol, side, size, order_type, price, client_order_id)
        assert_live_routing_blocked()
        raise AssertionError("unreachable")  # pragma: no cover

    def cancel_order(self, order_id: str) -> Any:
        _ = order_id
        assert_live_routing_blocked()
        raise AssertionError("unreachable")  # pragma: no cover


class GatedBackendRouter:
    """Envuelve un A3Backend con live_gate antes de cualquier envío.

    ``assert_live_routing_blocked`` falla siempre (fail-closed), independientemente
    del flag ``LIVE_BLOCKED``; Fake/PyRofex no son alcanzables en research-prod.
    """

    def __init__(self, backend: A3Backend) -> None:
        self._backend = backend

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        size: str,
        order_type: str,
        price: str | None,
        client_order_id: str,
    ) -> A3OrderAckDTO:
        assert_live_routing_blocked()
        return self._backend.place_order(
            symbol=symbol,
            side=side,
            size=size,
            order_type=order_type,
            price=price,
            client_order_id=client_order_id,
        )

    def cancel_order(self, order_id: str) -> A3OrderAckDTO:
        assert_live_routing_blocked()
        return self._backend.cancel_order(order_id)
