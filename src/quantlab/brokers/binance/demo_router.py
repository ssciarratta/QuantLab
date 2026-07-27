"""Binance demo order routing (F101) — solo tras unlock LIVE.

Transport default: simulador local con precio mid (MD público opcional).
Nunca pega a ``api.binance.com`` para órdenes. Testnet remoto = fase siguiente
cuando el operador configure keys en env (sin pasarlas al agente).
"""

from __future__ import annotations

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
    """Router de órdenes demo Binance — exige unlock activo.

    Default: simulador local. Opt-in testnet: ``QUANTLAB_DEMO_USE_TESTNET=1``
    + keys ``BINANCE_DEMO_*``.
    """

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
            return BrokerAck(
                order_id=intent.replace_target_id or "",
                client_order_id=intent.intent_id,
                status="CANCELED",
                message="demo cancel (sim)",
                venue=self.venue_id,
            )
        if intent.intent_type is not IntentType.PLACE_ORDER:
            raise ValidationError(f"intent no soportado en demo: {intent.intent_type}")
        if intent.side is None or intent.quantity is None:
            raise ValidationError("PLACE_ORDER requiere side y quantity")

        from quantlab.brokers.binance.testnet_client import testnet_remote_enabled

        if testnet_remote_enabled():
            return self._submit_testnet(intent)
        return self._submit_local(intent)

    def _submit_local(self, intent: OrderIntent) -> BrokerAck:
        assert intent.side is not None and intent.quantity is not None
        symbol = intent.instrument_id.strip().upper()
        mid = self._price_lookup(symbol)
        fill_price = intent.price if intent.price is not None else mid
        if fill_price <= 0:
            raise ValidationError("precio de fill inválido")

        self._seq += 1
        order_id = f"BN-DEMO-{self._seq}-{uuid.uuid4().hex[:8]}"
        fill = {
            "order_id": order_id,
            "client_order_id": intent.intent_id,
            "symbol": symbol,
            "side": intent.side.value,
            "quantity": str(intent.quantity),
            "price": str(fill_price),
            "ts": datetime.now(tz=UTC).isoformat(),
            "transport": "local_demo_sim",
            "venue": self.venue_id,
        }
        self._fills.append(fill)
        return BrokerAck(
            order_id=order_id,
            client_order_id=intent.intent_id,
            status="FILLED",
            message=f"binance demo sim fill @ {fill_price}",
            venue=self.venue_id,
        )

    def _submit_testnet(self, intent: OrderIntent) -> BrokerAck:
        assert intent.side is not None and intent.quantity is not None
        from quantlab.brokers.binance.testnet_client import BinanceTestnetClient

        if intent.price is not None:
            raise ValidationError(
                "testnet remoto F102 solo MARKET (omití price en el body)"
            )
        symbol = intent.instrument_id.strip().upper()
        client = BinanceTestnetClient()
        result = client.place_market_order(
            symbol=symbol,
            side=intent.side.value.upper(),
            quantity=str(intent.quantity),
            client_order_id=intent.intent_id,
        )
        fill = {
            "order_id": result.order_id,
            "client_order_id": result.client_order_id,
            "symbol": result.symbol,
            "side": result.side.lower(),
            "quantity": str(intent.quantity),
            "price": None,
            "ts": datetime.now(tz=UTC).isoformat(),
            "transport": "binance_spot_testnet",
            "venue": self.venue_id,
            "exchange_status": result.status,
        }
        self._fills.append(fill)
        return BrokerAck(
            order_id=result.order_id,
            client_order_id=result.client_order_id,
            status=result.status,
            message=f"binance testnet {result.status}",
            venue=self.venue_id,
        )

    def recent_fills(self, *, limit: int = 20) -> list[dict[str, Any]]:
        if limit < 1 or limit > 200:
            raise ValidationError("limit debe estar entre 1 y 200")
        return list(self._fills[-limit:])

    def status(self) -> dict[str, Any]:
        from quantlab.brokers.binance.testnet_client import testnet_status

        tn = testnet_status()
        transport = (
            "binance_spot_testnet" if tn["remote_enabled"] else "local_demo_sim"
        )
        return {
            "ok": True,
            "venue": self.venue_id,
            "transport": transport,
            "n_fills": len(self._fills),
            "symbols": sorted(_DEFAULT_MIDS),
            "remote_testnet": bool(tn["remote_enabled"]),
            "testnet": tn,
            "note": (
                "Default: simulador local post-unlock. "
                "Remoto: QUANTLAB_DEMO_USE_TESTNET=1 + BINANCE_DEMO_API_KEY/SECRET."
            ),
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
