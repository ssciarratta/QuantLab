"""Fachada A3Adapter — Data + Execution con gates."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType, OrderType
from quantlab.core.types.instrument import Instrument
from quantlab.core.types.manifests import DatasetManifest, TimeRange
from quantlab.core.types.market import Bar, Trade
from quantlab.core.types.orders import OrderIntent
from quantlab.core.types.serialization import dataclass_to_dict
from quantlab.data.catalog.catalog import DataCatalog
from quantlab.data.exchanges.a3.config import A3Config, live_trading_env_enabled
from quantlab.data.exchanges.a3.constants import PROVIDER_ID, SCHEMA_VERSION_BARS
from quantlab.data.exchanges.a3.exceptions import (
    A3LiveTradingDisabledError,
    A3RiskRejectedError,
)
from quantlab.data.exchanges.a3.kill_switch import KillSwitch
from quantlab.data.exchanges.a3.mappers import (
    A3SymbolMapper,
    instrument_dto_to_domain,
    trade_dto_to_domain,
)
from quantlab.data.exchanges.a3.models import (
    A3AccountSummaryDTO,
    A3MarketSnapshotDTO,
    A3OrderAckDTO,
    A3PositionDTO,
)
from quantlab.data.exchanges.a3.protocols import A3Backend
from quantlab.data.exchanges.a3.risk import DefaultPreTradeRiskGate, TradingContext
from quantlab.data.exchanges.a3.websocket import A3WebSocketCapture
from quantlab.data.normalization.bars import build_bars_from_trades
from quantlab.data.quality.validators import validate_bars, validate_trades
from quantlab.data.storage.raw_store import ProcessedStore, RawStore
from quantlab.execution.live_gate import assert_live_routing_blocked
from quantlab.execution.order_router import NullRouter, OrderRouter
from quantlab.infra.logging import get_logger

logger = get_logger(__name__)


class A3Adapter:
    """Adaptador anticorrupción A3. El dominio no ve pyRofex."""

    def __init__(
        self,
        config: A3Config,
        backend: A3Backend,
        *,
        account: str = "unknown",
        order_router: OrderRouter | None = None,
    ) -> None:
        self._config = config
        self._backend = backend
        self._account = account
        # Default NullRouter: market-data vía backend; órdenes nunca salen.
        self._order_router: OrderRouter = order_router or NullRouter()
        self._mapper = A3SymbolMapper()
        self._raw = RawStore(config.storage.raw_root)
        self._processed = ProcessedStore(config.storage.processed_root)
        self._catalog = DataCatalog(config.storage.catalog_path)
        self._kill = KillSwitch(config.storage.kill_switch_path)
        self._risk = DefaultPreTradeRiskGate(config, self._kill)
        self._ws = A3WebSocketCapture(maxsize=config.market_data.queue_maxsize)
        self._last_md_at: datetime | None = None
        self._last_price: Decimal | None = None
        self._open_client_ids: set[str] = set()
        self._run_id = str(uuid.uuid4())

    @staticmethod
    def _enforce_live_blocked() -> None:
        try:
            assert_live_routing_blocked()
        except ValidationError as exc:
            raise A3LiveTradingDisabledError(str(exc)) from exc

    def connect(self) -> None:
        self._backend.connect()
        logger.info("a3_connected", environment=self._config.environment.value)

    def close(self) -> None:
        self._backend.close()
        logger.info("a3_closed")

    def health_check(self) -> dict[str, Any]:
        return self._backend.health_check()

    def get_instruments(self) -> list[Instrument]:
        dtos = self._backend.get_instruments()
        self._raw.append(
            kind="instruments",
            environment=self._config.environment.value,
            symbol=None,
            endpoint_or_message_type="get_instruments",
            payload={"count": len(dtos), "symbols": [d.symbol for d in dtos]},
            ingestion_run_id=self._run_id,
        )
        return [instrument_dto_to_domain(d) for d in dtos]

    def get_instrument_details(self, symbol: str) -> Instrument:
        dto = self._backend.get_instrument_details(symbol)
        self._raw.append(
            kind="instruments",
            environment=self._config.environment.value,
            symbol=symbol,
            endpoint_or_message_type="get_instrument_details",
            payload=dto.raw,
            ingestion_run_id=self._run_id,
        )
        return instrument_dto_to_domain(dto)

    def get_market_snapshot(self, symbol: str) -> A3MarketSnapshotDTO:
        snap = self._backend.get_market_snapshot(symbol, depth=self._config.market_data.depth)
        self._last_md_at = snap.timestamp
        self._last_price = snap.last_price
        self._raw.append(
            kind="market_data",
            environment=self._config.environment.value,
            symbol=symbol,
            endpoint_or_message_type="get_market_snapshot",
            payload=snap.raw,
            event_timestamp=snap.timestamp,
            ingestion_run_id=self._run_id,
        )
        return snap

    def get_historical_trades(self, symbol: str, start: datetime, end: datetime) -> list[Trade]:
        dtos = self._backend.get_historical_trades(symbol, start, end)
        if dtos:
            self._raw.append(
                kind="trades",
                environment=self._config.environment.value,
                symbol=symbol,
                endpoint_or_message_type="get_historical_trades",
                payload={"count": len(dtos), "trades": [d.raw for d in dtos]},
                event_timestamp=dtos[0].timestamp,
                ingestion_run_id=self._run_id,
            )
        trades = [trade_dto_to_domain(d) for d in dtos]
        report = validate_trades(trades)
        if report.has_fatal:
            logger.error("trade_quality_fatal", issues=[i.code for i in report.issues])
        return trades

    def get_historical_bars(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> tuple[tuple[Bar, ...], DatasetManifest]:
        trades = self.get_historical_trades(symbol, start, end)
        build = build_bars_from_trades(trades, timeframe=timeframe, instrument_id=f"a3:{symbol}")
        q = validate_bars(list(build.bars))
        rows = [dataclass_to_dict(b) for b in build.bars]
        dataset_id = f"a3-bars-{self._mapper.to_path_safe(symbol)}-{timeframe}"
        path = self._processed.write_jsonl(
            dataset_id=dataset_id,
            schema_version=SCHEMA_VERSION_BARS,
            symbol=symbol,
            timeframe=timeframe,
            rows=rows,
            meta={
                "gaps": list(build.gaps),
                "duplicate_trades_removed": build.duplicate_trades_removed,
                "incomplete_last_bar": build.incomplete_last_bar,
                "quality": [i.code for i in q.issues],
            },
        )
        # Checksum del storage real (verify_dataset hashea el archivo).
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        now = datetime.now(tz=UTC)
        tr = TimeRange(start=start if start.tzinfo else start.replace(tzinfo=UTC), end=end)
        manifest = DatasetManifest(
            dataset_id=dataset_id,
            version="v1",
            source=PROVIDER_ID,
            instruments=(f"a3:{symbol}",),
            time_range=tr,
            granularity=timeframe,
            schema_version=SCHEMA_VERSION_BARS,
            checksum=checksum,
            row_count=len(build.bars),
            storage_path=str(path),
            created_at=now,
        )
        self._catalog.register_dataset(manifest, kind="bars", provider=PROVIDER_ID)
        return build.bars, manifest

    def subscribe_market_data(self, symbols: list[str]) -> CallableHandler:
        """Devuelve handler listo para registrar en WS real; en tests se usa directo."""
        return CallableHandler(self._ws.make_handler("market_data"), symbols)

    def unsubscribe_market_data(self, symbols: list[str]) -> None:
        logger.info("a3_unsubscribe", symbols=symbols)

    def place_order(self, order_intent: OrderIntent) -> A3OrderAckDTO:
        # Fail-closed universal (research-prod): antes de risk/backend.
        self._enforce_live_blocked()
        if order_intent.intent_type is not IntentType.PLACE_ORDER:
            raise A3RiskRejectedError("place_order requiere PLACE_ORDER")

        ctx = TradingContext(
            environment=self._config.environment.value,
            account=self._account,
            is_production=self._config.is_production,
            execution_enabled=self._config.execution.enabled,
            allow_live_orders=self._config.execution.allow_live_orders,
            live_env_confirmed=live_trading_env_enabled(),
            last_market_data_at=self._last_md_at,
            last_price=self._last_price,
            open_client_order_ids=frozenset(self._open_client_ids),
        )

        if self._config.is_production and (
            not self._config.execution.allow_live_orders or not live_trading_env_enabled()
        ):
            raise A3LiveTradingDisabledError("order routing real BLOQUEADO")

        decision = self._risk.evaluate(order_intent, ctx)
        if not decision.approved:
            logger.warning("a3_risk_rejected", reasons=list(decision.reasons))
            raise A3RiskRejectedError(";".join(decision.reasons))

        symbol = order_intent.instrument_id.removeprefix("a3:")
        side = order_intent.side.value if order_intent.side else "buy"
        otype = "limit"
        if order_intent.order_type is OrderType.MARKET:
            otype = "market"
        price = str(order_intent.price) if order_intent.price is not None else None
        size = str(order_intent.quantity) if order_intent.quantity is not None else "0"

        # NullRouter / GatedBackendRouter — nunca bypasea live_gate.
        ack = self._order_router.place_order(
            symbol=symbol,
            side=side,
            size=size,
            order_type=otype,
            price=price,
            client_order_id=order_intent.intent_id,
        )
        self._open_client_ids.add(order_intent.intent_id)
        self._raw.append(
            kind="executions",
            environment=self._config.environment.value,
            symbol=symbol,
            endpoint_or_message_type="place_order",
            payload=ack.raw,
            request_id=order_intent.intent_id,
            ingestion_run_id=self._run_id,
        )
        logger.info(
            "a3_order_placed",
            environment=self._config.environment.value,
            symbol=symbol,
            client_order_id=order_intent.intent_id,
            order_id=ack.order_id,
        )
        return ack

    def cancel_order(self, order_id: str) -> A3OrderAckDTO:
        self._enforce_live_blocked()
        status = self._backend.get_order_status(order_id)
        if status.status.upper() in {"CANCELED", "CANCELLED", "FILLED", "REJECTED"}:
            return status
        ack = self._order_router.cancel_order(order_id)
        confirmed = self._backend.get_order_status(order_id)
        self._raw.append(
            kind="executions",
            environment=self._config.environment.value,
            symbol=confirmed.symbol,
            endpoint_or_message_type="cancel_order",
            payload=confirmed.raw,
            request_id=order_id,
            ingestion_run_id=self._run_id,
        )
        return confirmed if confirmed.status else ack

    def get_order_status(self, order_id: str) -> A3OrderAckDTO:
        return self._backend.get_order_status(order_id)

    def get_orders(self) -> list[A3OrderAckDTO]:
        return self._backend.get_orders()

    def get_account_summary(self) -> A3AccountSummaryDTO:
        return self._backend.get_account_summary()

    def get_positions(self) -> list[A3PositionDTO]:
        return self._backend.get_positions()

    @property
    def catalog(self) -> DataCatalog:
        return self._catalog

    @property
    def websocket_capture(self) -> A3WebSocketCapture:
        return self._ws


class CallableHandler:
    def __init__(self, handler: Any, symbols: list[str]) -> None:
        self.handler = handler
        self.symbols = symbols
