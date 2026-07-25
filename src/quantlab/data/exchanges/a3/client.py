"""Wrapper pyRofex — único punto que importa la librería externa."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from quantlab.data.exchanges.a3.config import A3Credentials
from quantlab.data.exchanges.a3.constants import A3EnvironmentName
from quantlab.data.exchanges.a3.exceptions import (
    A3AuthenticationError,
    A3ConnectionError,
    A3ProtocolError,
)
from quantlab.data.exchanges.a3.mappers import (
    parse_instrument_dto,
    parse_snapshot_dto,
    parse_trade_dto,
)
from quantlab.data.exchanges.a3.models import (
    A3AccountSummaryDTO,
    A3InstrumentDTO,
    A3MarketSnapshotDTO,
    A3OrderAckDTO,
    A3PositionDTO,
    A3TradeDTO,
)


def _map_environment(name: A3EnvironmentName) -> Any:
    import pyRofex

    if name is A3EnvironmentName.SIMULATION:
        return pyRofex.Environment.REMARKET
    return pyRofex.Environment.LIVE


class PyRofexBackend:
    """Backend real. No usar en CI sin credenciales."""

    def __init__(self, credentials: A3Credentials, environment: A3EnvironmentName) -> None:
        self._credentials = credentials
        self._environment = environment
        self._connected = False

    def connect(self) -> None:
        import pyRofex

        try:
            pyRofex.initialize(
                user=self._credentials.user,
                password=self._credentials.password,
                account=self._credentials.account,
                environment=_map_environment(self._environment),
                active_token=self._credentials.token,
            )
        except Exception as exc:  # frontera externa
            raise A3AuthenticationError("fallo initialize pyRofex") from exc
        self._connected = True

    def close(self) -> None:
        try:
            import pyRofex

            pyRofex.close_websocket_connection()
        except Exception:
            pass
        self._connected = False

    def health_check(self) -> dict[str, Any]:
        return {
            "ok": self._connected,
            "provider": "pyRofex",
            "environment": self._environment.value,
        }

    def get_instruments(self) -> list[A3InstrumentDTO]:
        import pyRofex

        try:
            raw = pyRofex.get_all_instruments()
        except Exception as exc:
            raise A3ConnectionError("get_all_instruments falló") from exc
        instruments = raw.get("instruments", raw) if isinstance(raw, dict) else raw
        if not isinstance(instruments, list):
            raise A3ProtocolError("instruments response inesperada")
        return [parse_instrument_dto(item) for item in instruments if isinstance(item, dict)]

    def get_instrument_details(self, symbol: str) -> A3InstrumentDTO:
        import pyRofex

        try:
            raw = pyRofex.get_instrument_details(ticker=symbol)
        except Exception as exc:
            raise A3ConnectionError("get_instrument_details falló") from exc
        if isinstance(raw, dict) and "instrument" in raw:
            raw = raw["instrument"]
        if not isinstance(raw, dict):
            raise A3ProtocolError("instrument details inesperado")
        return parse_instrument_dto(raw)

    def get_market_snapshot(self, symbol: str, depth: int = 5) -> A3MarketSnapshotDTO:
        import pyRofex

        try:
            raw = pyRofex.get_market_data(ticker=symbol, depth=depth)
        except Exception as exc:
            raise A3ConnectionError("get_market_data falló") from exc
        if not isinstance(raw, dict):
            raise A3ProtocolError("market data inesperado")
        return parse_snapshot_dto(symbol, raw)

    def get_historical_trades(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[A3TradeDTO]:
        import pyRofex

        try:
            raw = pyRofex.get_trade_history(
                ticker=symbol,
                start_date=start.strftime("%Y-%m-%d"),
                end_date=end.strftime("%Y-%m-%d"),
            )
        except Exception as exc:
            raise A3ConnectionError("get_trade_history falló") from exc
        trades = raw.get("trades", raw) if isinstance(raw, dict) else raw
        if not isinstance(trades, list):
            raise A3ProtocolError("trade history inesperado")
        return [parse_trade_dto(symbol, item) for item in trades if isinstance(item, dict)]

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
        from quantlab.execution.live_gate import assert_live_routing_blocked

        assert_live_routing_blocked()
        import pyRofex

        side_enum = pyRofex.Side.BUY if side.lower() == "buy" else pyRofex.Side.SELL
        type_enum = pyRofex.OrderType.LIMIT
        if order_type == "market":
            type_enum = pyRofex.OrderType.MARKET
        try:
            raw = pyRofex.send_order(
                ticker=symbol,
                size=float(size),
                order_type=type_enum,
                side=side_enum,
                price=float(price) if price is not None else None,
            )
        except Exception as exc:
            raise A3ConnectionError("send_order falló") from exc
        if not isinstance(raw, dict):
            raise A3ProtocolError("send_order response inesperada")
        order_id = str(raw.get("orderId") or raw.get("order", {}).get("orderId") or "")
        return A3OrderAckDTO(
            client_order_id=client_order_id,
            order_id=order_id or None,
            status=str(raw.get("status") or "PENDING"),
            symbol=symbol,
            raw=raw,
        )

    def cancel_order(self, order_id: str) -> A3OrderAckDTO:
        from quantlab.execution.live_gate import assert_live_routing_blocked

        assert_live_routing_blocked()
        import pyRofex

        try:
            raw = pyRofex.cancel_order(id=order_id)
        except Exception as exc:
            raise A3ConnectionError("cancel_order falló") from exc
        if not isinstance(raw, dict):
            raw = {"raw": raw}
        return A3OrderAckDTO(
            client_order_id=order_id,
            order_id=order_id,
            status=str(raw.get("status") or "CANCEL_REQUESTED"),
            symbol=str(raw.get("symbol") or ""),
            raw=raw if isinstance(raw, dict) else {},
        )

    def get_order_status(self, order_id: str) -> A3OrderAckDTO:
        import pyRofex

        try:
            raw = pyRofex.get_order_status(id=order_id)
        except Exception as exc:
            raise A3ConnectionError("get_order_status falló") from exc
        if not isinstance(raw, dict):
            raise A3ProtocolError("order status inesperado")
        return A3OrderAckDTO(
            client_order_id=str(raw.get("clOrdId") or order_id),
            order_id=order_id,
            status=str(raw.get("status") or raw.get("orderStatus") or "UNKNOWN"),
            symbol=str(raw.get("symbol") or ""),
            raw=raw,
        )

    def get_orders(self) -> list[A3OrderAckDTO]:
        import pyRofex

        try:
            raw = pyRofex.get_all_orders_status()
        except Exception as exc:
            raise A3ConnectionError("get_all_orders_status falló") from exc
        orders = raw.get("orders", []) if isinstance(raw, dict) else []
        result: list[A3OrderAckDTO] = []
        for item in orders:
            if not isinstance(item, dict):
                continue
            oid = str(item.get("orderId") or item.get("id") or "")
            result.append(
                A3OrderAckDTO(
                    client_order_id=str(item.get("clOrdId") or oid),
                    order_id=oid or None,
                    status=str(item.get("status") or "UNKNOWN"),
                    symbol=str(item.get("symbol") or ""),
                    raw=item,
                )
            )
        return result

    def get_account_summary(self) -> A3AccountSummaryDTO:
        import pyRofex

        try:
            raw = pyRofex.get_account_report()
        except Exception as exc:
            raise A3ConnectionError("get_account_report falló") from exc
        if not isinstance(raw, dict):
            raise A3ProtocolError("account report inesperado")
        return A3AccountSummaryDTO(
            account=self._credentials.account,
            currency=None,
            available=Decimal(str(raw["available"])) if raw.get("available") is not None else None,
            raw=raw,
        )

    def get_positions(self) -> list[A3PositionDTO]:
        import pyRofex

        try:
            raw = pyRofex.get_account_position()
        except Exception as exc:
            raise A3ConnectionError("get_account_position falló") from exc
        positions = raw.get("positions", raw) if isinstance(raw, dict) else raw
        if not isinstance(positions, list):
            return []
        out: list[A3PositionDTO] = []
        for item in positions:
            if not isinstance(item, dict):
                continue
            sym = str(item.get("symbol") or item.get("instrument") or "")
            qty = item.get("netSize") or item.get("size") or 0
            out.append(
                A3PositionDTO(
                    symbol=sym,
                    quantity=Decimal(str(qty)),
                    avg_price=None,
                    raw=item,
                )
            )
        return out
