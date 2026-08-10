"""Binance demo order routing (F101+) — solo tras unlock LIVE.

Transport default: simulador local con precio mid (MD público opcional).
Nunca pega a ``api.binance.com`` para órdenes. Testnet remoto = opt-in F102.
"""

from __future__ import annotations

import contextlib
import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.brokers.types import BrokerAck
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import require_live_unlock

PriceLookup = Callable[[str], Decimal]

_DEFAULT_MIDS: dict[str, Decimal] = {
    "BTCUSDT": Decimal("60000"),
    "ETHUSDT": Decimal("3000"),
    "BNBUSDT": Decimal("500"),
}

_router_lock = threading.RLock()
_shared_router: BinanceDemoRouter | None = None


def _parse_decimal(raw: object, *, field: str) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValidationError(f"{field} inválido") from exc
    if not value.is_finite() or value <= 0:
        raise ValidationError(f"{field} debe ser Decimal finito > 0")
    return value


def default_mid_price(symbol: str) -> Decimal:
    """Mid de tabla local; fail-closed si el símbolo no está en el catálogo demo."""
    key = symbol.strip().upper()
    if key in _DEFAULT_MIDS:
        return _DEFAULT_MIDS[key]
    raise ValidationError(
        f"símbolo demo no soportado: {symbol!r} "
        f"(válidos: {', '.join(sorted(_DEFAULT_MIDS))})"
    )


class BinanceDemoRouter:
    """Router de órdenes demo Binance — exige unlock activo."""

    venue_id: str = "binance_demo"

    def __init__(
        self,
        *,
        price_lookup: PriceLookup | None = None,
        require_unlock: bool = True,
    ) -> None:
        if require_unlock:
            require_live_unlock(venue_scope="binance_demo")
        self._price_lookup = price_lookup or default_mid_price
        self._seq = 0
        self._fills: list[dict[str, Any]] = []
        self._open_orders: dict[str, dict[str, Any]] = {}

    def submit(self, intent: OrderIntent) -> BrokerAck:
        require_live_unlock(venue_scope="binance_demo")
        if intent.intent_type is IntentType.NO_ACTION:
            return BrokerAck(
                order_id="",
                client_order_id=intent.intent_id,
                status="NO_ACTION",
                message="no-op",
                venue=self.venue_id,
            )
        if intent.intent_type is IntentType.CANCEL_ORDER:
            return self.cancel(intent.replace_target_id or "")
        if intent.intent_type is not IntentType.PLACE_ORDER:
            raise ValidationError(f"intent no soportado en demo: {intent.intent_type}")
        if intent.side is None or intent.quantity is None:
            raise ValidationError("PLACE_ORDER requiere side y quantity")

        from quantlab.brokers.binance.demo_transport import resolve_demo_transport

        transport = resolve_demo_transport(unlocked=True)
        if transport == "binance_spot_testnet":
            return self._submit_spot_testnet(intent)
        if transport == "binance_futures_testnet":
            return self._submit_futures_testnet(intent)
        return self._submit_local(intent)

    def cancel(self, order_id: str) -> BrokerAck:
        require_live_unlock(venue_scope="binance_demo")
        oid = order_id.strip()
        if not oid:
            raise ValidationError("order_id requerido para cancel")
        if oid not in self._open_orders:
            return BrokerAck(
                order_id=oid,
                client_order_id=f"cancel-{uuid.uuid4().hex[:8]}",
                status="REJECTED",
                message="orden demo no encontrada o ya cerrada",
                venue=self.venue_id,
            )
        open_order = self._open_orders.pop(oid)
        exchange_oid = open_order.get("exchange_order_id")
        transport = str(open_order.get("transport") or "")
        if exchange_oid:
            if transport == "binance_spot_testnet":
                from quantlab.brokers.binance.testnet_client import BinanceTestnetClient

                BinanceTestnetClient().cancel_order(
                    symbol=str(open_order["symbol"]),
                    order_id=str(exchange_oid),
                )
            elif transport == "binance_futures_testnet":
                from quantlab.brokers.binance.futures_testnet_client import (
                    BinanceFuturesTestnetClient,
                )

                BinanceFuturesTestnetClient().cancel_order(
                    symbol=str(open_order["symbol"]),
                    order_id=str(exchange_oid),
                )
        return BrokerAck(
            order_id=oid,
            client_order_id=f"cancel-{uuid.uuid4().hex[:8]}",
            status="CANCELED",
            message="demo cancel ok",
            venue=self.venue_id,
        )

    def _next_order_id(self) -> str:
        self._seq += 1
        return f"BN-DEMO-{self._seq}-{uuid.uuid4().hex[:8]}"

    def _limit_marketable(
        self, side: OrderSide, limit: Decimal, mid: Decimal
    ) -> bool:
        if side is OrderSide.BUY:
            return limit >= mid
        return limit <= mid

    def _record_fill(
        self,
        *,
        order_id: str,
        intent: OrderIntent,
        symbol: str,
        fill_price: Decimal,
        transport: str,
        exchange_status: str | None = None,
        exchange_order_id: str | None = None,
    ) -> dict[str, Any]:
        assert intent.side is not None and intent.quantity is not None
        fill = {
            "order_id": order_id,
            "client_order_id": intent.intent_id,
            "symbol": symbol,
            "side": intent.side.value,
            "quantity": str(intent.quantity),
            "price": str(fill_price),
            "ts": datetime.now(tz=UTC).isoformat(),
            "transport": transport,
            "venue": self.venue_id,
        }
        if exchange_status is not None:
            fill["exchange_status"] = exchange_status
        if exchange_order_id is not None:
            fill["exchange_order_id"] = exchange_order_id
        self._fills.append(fill)
        return fill

    def _submit_local(self, intent: OrderIntent) -> BrokerAck:
        assert intent.side is not None and intent.quantity is not None
        symbol = intent.instrument_id.strip().upper()
        mid = self._price_lookup(symbol)
        order_id = self._next_order_id()

        if intent.order_type is OrderType.LIMIT and intent.price is not None:
            limit = intent.price
            if not self._limit_marketable(intent.side, limit, mid):
                self._open_orders[order_id] = {
                    "order_id": order_id,
                    "client_order_id": intent.intent_id,
                    "symbol": symbol,
                    "side": intent.side.value,
                    "quantity": str(intent.quantity),
                    "price": str(limit),
                    "order_type": "limit",
                    "status": "NEW",
                    "ts": datetime.now(tz=UTC).isoformat(),
                    "transport": "local_demo_sim",
                }
                return BrokerAck(
                    order_id=order_id,
                    client_order_id=intent.intent_id,
                    status="NEW",
                    message=f"limit resting @ {limit} (mid={mid})",
                    venue=self.venue_id,
                )
            fill_price = limit
        else:
            fill_price = mid

        if fill_price <= 0:
            raise ValidationError("precio de fill inválido")

        self._record_fill(
            order_id=order_id,
            intent=intent,
            symbol=symbol,
            fill_price=fill_price,
            transport="local_demo_sim",
        )
        return BrokerAck(
            order_id=order_id,
            client_order_id=intent.intent_id,
            status="FILLED",
            message=f"binance demo sim fill @ {fill_price}",
            venue=self.venue_id,
        )

    def _submit_remote_order(
        self,
        intent: OrderIntent,
        *,
        transport: str,
        id_prefix: str,
        place_limit: Any,
        place_market: Any,
    ) -> BrokerAck:
        assert intent.side is not None and intent.quantity is not None
        symbol = intent.instrument_id.strip().upper()
        if intent.order_type is OrderType.LIMIT and intent.price is not None:
            result = place_limit(
                symbol=symbol,
                side=intent.side.value.upper(),
                quantity=str(intent.quantity),
                price=str(intent.price),
                client_order_id=intent.intent_id,
            )
            raw_id = result.order_id.removeprefix(id_prefix)
            if result.status in {"NEW", "PARTIALLY_FILLED"}:
                self._open_orders[result.order_id] = {
                    "order_id": result.order_id,
                    "client_order_id": result.client_order_id,
                    "symbol": symbol,
                    "side": intent.side.value,
                    "quantity": str(intent.quantity),
                    "price": str(intent.price),
                    "order_type": "limit",
                    "status": result.status,
                    "exchange_order_id": raw_id,
                    "transport": transport,
                }
                return BrokerAck(
                    order_id=result.order_id,
                    client_order_id=result.client_order_id,
                    status=result.status,
                    message=f"{transport} limit {result.status}",
                    venue=self.venue_id,
                )
            fill_price = intent.price
        else:
            result = place_market(
                symbol=symbol,
                side=intent.side.value.upper(),
                quantity=str(intent.quantity),
                client_order_id=intent.intent_id,
            )
            fill_price = (
                intent.price if intent.price is not None else self._price_lookup(symbol)
            )
            raw = result.raw
            fills = raw.get("fills") if isinstance(raw.get("fills"), list) else []
            if fills and isinstance(fills[0], dict) and fills[0].get("price"):
                fill_price = _parse_decimal(fills[0]["price"], field="fill_price")
            avg = raw.get("avgPrice")
            if avg not in (None, "", "0", "0.0", "0.00000000"):
                with contextlib.suppress(ValidationError):
                    fill_price = _parse_decimal(avg, field="avgPrice")

        if result.status not in {"FILLED", "PARTIALLY_FILLED"}:
            return BrokerAck(
                order_id=result.order_id,
                client_order_id=result.client_order_id,
                status=result.status,
                message=f"{transport} {result.status}",
                venue=self.venue_id,
            )

        self._record_fill(
            order_id=result.order_id,
            intent=intent,
            symbol=result.symbol,
            fill_price=fill_price,
            transport=transport,
            exchange_status=result.status,
            exchange_order_id=result.order_id.removeprefix(id_prefix),
        )
        return BrokerAck(
            order_id=result.order_id,
            client_order_id=result.client_order_id,
            status=result.status,
            message=f"{transport} {result.status}",
            venue=self.venue_id,
        )

    def _submit_spot_testnet(self, intent: OrderIntent) -> BrokerAck:
        from quantlab.brokers.binance.testnet_client import BinanceTestnetClient

        client = BinanceTestnetClient()
        return self._submit_remote_order(
            intent,
            transport="binance_spot_testnet",
            id_prefix="BN-TN-",
            place_limit=client.place_limit_order,
            place_market=client.place_market_order,
        )

    def _submit_futures_testnet(self, intent: OrderIntent) -> BrokerAck:
        from quantlab.brokers.binance.futures_testnet_client import (
            BinanceFuturesTestnetClient,
        )

        client = BinanceFuturesTestnetClient()
        return self._submit_remote_order(
            intent,
            transport="binance_futures_testnet",
            id_prefix="BN-FUT-TN-",
            place_limit=client.place_limit_order,
            place_market=client.place_market_order,
        )

    def open_orders(self) -> list[dict[str, Any]]:
        return list(self._open_orders.values())

    def recent_fills(self, *, limit: int = 20) -> list[dict[str, Any]]:
        if limit < 1 or limit > 200:
            raise ValidationError("limit debe estar entre 1 y 200")
        return list(self._fills[-limit:])

    def status(self) -> dict[str, Any]:
        from quantlab.brokers.binance.demo_transport import demo_transport_status

        dt = demo_transport_status(unlocked=True)
        transport = dt.get("transport") or "local_demo_sim"
        remote = transport in {
            "binance_spot_testnet",
            "binance_futures_testnet",
        }
        return {
            "ok": dt.get("error") is None,
            "venue": self.venue_id,
            "transport": transport,
            "n_fills": len(self._fills),
            "n_open_orders": len(self._open_orders),
            "symbols": sorted(_DEFAULT_MIDS),
            "remote_testnet": remote,
            "remote_market": (
                "spot"
                if transport == "binance_spot_testnet"
                else "futures"
                if transport == "binance_futures_testnet"
                else None
            ),
            "testnet": dt.get("spot"),
            "futures_testnet": dt.get("futures"),
            "conflict": bool(dt.get("conflict")),
            "error": dt.get("error"),
            "note": dt.get("note"),
        }


def get_shared_demo_router() -> BinanceDemoRouter:
    """Router de proceso (fills acumulados mientras el unlock viva)."""
    global _shared_router
    require_live_unlock(venue_scope="binance_demo")
    with _router_lock:
        if _shared_router is None:
            _shared_router = BinanceDemoRouter(require_unlock=True)
        return _shared_router


def reset_demo_router() -> None:
    """Cierra el router compartido (lock LIVE / tests)."""
    global _shared_router
    with _router_lock:
        _shared_router = None


def intent_from_demo_body(body: dict[str, Any]) -> OrderIntent:
    """Construye OrderIntent desde payload API demo (fail-closed)."""
    intent_type_raw = body.get("intent_type", "place_order")
    if intent_type_raw == "cancel_order":
        order_id = body.get("order_id")
        if not isinstance(order_id, str) or not order_id.strip():
            raise ValidationError("order_id requerido para cancel_order")
        return OrderIntent(
            intent_id=f"cancel-{uuid.uuid4().hex[:12]}",
            intent_type=IntentType.CANCEL_ORDER,
            instrument_id="__demo_cancel__",
            replace_target_id=order_id.strip(),
        )

    symbol = body.get("symbol")
    side_raw = body.get("side")
    qty_raw = body.get("quantity")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValidationError("symbol requerido")
    if not isinstance(side_raw, str):
        raise ValidationError("side requerido (BUY|SELL)")
    try:
        side = OrderSide(side_raw.strip().lower())
    except ValueError as exc:
        raise ValidationError("side inválido (BUY|SELL)") from exc
    quantity = _parse_decimal(qty_raw, field="quantity")
    price_raw = body.get("price")
    price: Decimal | None = None
    if price_raw is not None and price_raw != "":
        price = _parse_decimal(price_raw, field="price")
    intent_id = body.get("client_order_id")
    if not isinstance(intent_id, str) or not intent_id.strip():
        intent_id = f"demo-{uuid.uuid4().hex[:12]}"
    if price is None:
        order_type = OrderType.MARKET
        tif: TimeInForce | None = None
    else:
        order_type = OrderType.LIMIT
        tif = TimeInForce.GTC
    return OrderIntent(
        intent_id=intent_id.strip(),
        intent_type=IntentType.PLACE_ORDER,
        instrument_id=symbol.strip().upper(),
        side=side,
        quantity=quantity,
        price=price,
        order_type=order_type,
        time_in_force=tif,
    )
