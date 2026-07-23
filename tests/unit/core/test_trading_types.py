"""Tests for trading domain types — OrderIntent, Balance, TimeRange, etc."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import MappingProxyType

import pytest

from quantlab.core.types.market import (
    Instrument,
    OrderSide,
    OrderType,
)
from quantlab.core.types.trading import (
    Balance,
    IntentType,
    MarketEvent,
    MarketEventType,
    MetricsResult,
    OrderIntent,
    SimulationResult,
    StrategyContext,
    TimeRange,
)


class TestOrderIntentPlaceOrder:
    @pytest.fixture
    def instrument(self):
        return Instrument.create(
            symbol="BTC-USDT",
            base_asset="BTC",
            quote_asset="USDT",
            tick_size=0.01,
            lot_size=0.001,
        )

    def test_valid_limit_order(self, instrument):
        intent = OrderIntent(
            intent_type=IntentType.PLACE_ORDER,
            instrument=instrument,
            side=OrderSide.BUY,
            quantity=1.0,
            order_type=OrderType.LIMIT,
            price=50000.0,
        )
        assert intent.intent_type == IntentType.PLACE_ORDER

    def test_valid_market_order(self, instrument):
        intent = OrderIntent(
            intent_type=IntentType.PLACE_ORDER,
            instrument=instrument,
            side=OrderSide.SELL,
            quantity=0.5,
            order_type=OrderType.MARKET,
        )
        assert intent.price is None

    def test_missing_instrument(self):
        with pytest.raises(ValueError, match="instrument"):
            OrderIntent(
                intent_type=IntentType.PLACE_ORDER,
                side=OrderSide.BUY,
                quantity=1.0,
                order_type=OrderType.LIMIT,
                price=50000.0,
            )

    def test_missing_side(self, instrument):
        with pytest.raises(ValueError, match="side"):
            OrderIntent(
                intent_type=IntentType.PLACE_ORDER,
                instrument=instrument,
                quantity=1.0,
                order_type=OrderType.LIMIT,
                price=50000.0,
            )

    def test_missing_quantity(self, instrument):
        with pytest.raises(ValueError, match="quantity"):
            OrderIntent(
                intent_type=IntentType.PLACE_ORDER,
                instrument=instrument,
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=50000.0,
            )

    def test_zero_quantity_rejected(self, instrument):
        with pytest.raises(ValueError, match="quantity"):
            OrderIntent(
                intent_type=IntentType.PLACE_ORDER,
                instrument=instrument,
                side=OrderSide.BUY,
                quantity=0.0,
                order_type=OrderType.LIMIT,
                price=50000.0,
            )

    def test_negative_quantity_rejected(self, instrument):
        with pytest.raises(ValueError, match="quantity"):
            OrderIntent(
                intent_type=IntentType.PLACE_ORDER,
                instrument=instrument,
                side=OrderSide.BUY,
                quantity=-1.0,
                order_type=OrderType.LIMIT,
                price=50000.0,
            )

    def test_limit_without_price(self, instrument):
        with pytest.raises(ValueError, match="price"):
            OrderIntent(
                intent_type=IntentType.PLACE_ORDER,
                instrument=instrument,
                side=OrderSide.BUY,
                quantity=1.0,
                order_type=OrderType.LIMIT,
            )

    def test_limit_with_zero_price(self, instrument):
        with pytest.raises(ValueError, match="price"):
            OrderIntent(
                intent_type=IntentType.PLACE_ORDER,
                instrument=instrument,
                side=OrderSide.BUY,
                quantity=1.0,
                order_type=OrderType.LIMIT,
                price=0.0,
            )

    def test_with_target_order_id_rejected(self, instrument):
        with pytest.raises(ValueError, match="target_order_id"):
            OrderIntent(
                intent_type=IntentType.PLACE_ORDER,
                instrument=instrument,
                side=OrderSide.BUY,
                quantity=1.0,
                order_type=OrderType.MARKET,
                target_order_id="ord-1",
            )

    def test_with_replacement_fields_rejected(self, instrument):
        with pytest.raises(ValueError, match="replacement"):
            OrderIntent(
                intent_type=IntentType.PLACE_ORDER,
                instrument=instrument,
                side=OrderSide.BUY,
                quantity=1.0,
                order_type=OrderType.MARKET,
                new_quantity=2.0,
            )


class TestOrderIntentCancelOrder:
    def test_valid_cancel(self):
        intent = OrderIntent(
            intent_type=IntentType.CANCEL_ORDER,
            target_order_id="ord-123",
        )
        assert intent.target_order_id == "ord-123"

    def test_missing_target(self):
        with pytest.raises(ValueError, match="target_order_id"):
            OrderIntent(intent_type=IntentType.CANCEL_ORDER)

    def test_empty_target_rejected(self):
        with pytest.raises(ValueError, match="target_order_id"):
            OrderIntent(
                intent_type=IntentType.CANCEL_ORDER,
                target_order_id="",
            )

    def test_incompatible_fields_rejected(self):
        with pytest.raises(ValueError, match="must not include"):
            OrderIntent(
                intent_type=IntentType.CANCEL_ORDER,
                target_order_id="ord-123",
                side=OrderSide.BUY,
            )

    def test_incompatible_price_rejected(self):
        with pytest.raises(ValueError, match="must not include"):
            OrderIntent(
                intent_type=IntentType.CANCEL_ORDER,
                target_order_id="ord-123",
                price=100.0,
            )


class TestOrderIntentReplaceOrder:
    def test_valid_replace_quantity(self):
        intent = OrderIntent(
            intent_type=IntentType.REPLACE_ORDER,
            target_order_id="ord-123",
            new_quantity=2.0,
        )
        assert intent.new_quantity == 2.0

    def test_valid_replace_price(self):
        intent = OrderIntent(
            intent_type=IntentType.REPLACE_ORDER,
            target_order_id="ord-123",
            new_price=55000.0,
        )
        assert intent.new_price == 55000.0

    def test_valid_replace_both(self):
        intent = OrderIntent(
            intent_type=IntentType.REPLACE_ORDER,
            target_order_id="ord-123",
            new_quantity=3.0,
            new_price=60000.0,
        )
        assert intent.new_quantity == 3.0
        assert intent.new_price == 60000.0

    def test_missing_target_rejected(self):
        with pytest.raises(ValueError, match="target_order_id"):
            OrderIntent(
                intent_type=IntentType.REPLACE_ORDER,
                new_quantity=2.0,
            )

    def test_no_new_values_rejected(self):
        with pytest.raises(ValueError, match="new_quantity or new_price"):
            OrderIntent(
                intent_type=IntentType.REPLACE_ORDER,
                target_order_id="ord-123",
            )

    def test_zero_new_quantity_rejected(self):
        with pytest.raises(ValueError, match="new_quantity"):
            OrderIntent(
                intent_type=IntentType.REPLACE_ORDER,
                target_order_id="ord-123",
                new_quantity=0.0,
            )

    def test_negative_new_price_rejected(self):
        with pytest.raises(ValueError, match="new_price"):
            OrderIntent(
                intent_type=IntentType.REPLACE_ORDER,
                target_order_id="ord-123",
                new_price=-1.0,
            )


class TestOrderIntentNoAction:
    def test_valid_no_action(self):
        intent = OrderIntent(intent_type=IntentType.NO_ACTION)
        assert intent.intent_type == IntentType.NO_ACTION

    def test_with_price_rejected(self):
        with pytest.raises(ValueError, match="must not contain"):
            OrderIntent(intent_type=IntentType.NO_ACTION, price=100.0)

    def test_with_quantity_rejected(self):
        with pytest.raises(ValueError, match="must not contain"):
            OrderIntent(intent_type=IntentType.NO_ACTION, quantity=1.0)

    def test_with_side_rejected(self):
        with pytest.raises(ValueError, match="must not contain"):
            OrderIntent(intent_type=IntentType.NO_ACTION, side=OrderSide.BUY)

    def test_with_order_type_rejected(self):
        with pytest.raises(ValueError, match="must not contain"):
            OrderIntent(intent_type=IntentType.NO_ACTION, order_type=OrderType.LIMIT)

    def test_with_target_rejected(self):
        with pytest.raises(ValueError, match="must not contain"):
            OrderIntent(
                intent_type=IntentType.NO_ACTION,
                target_order_id="ord-1",
            )

    def test_with_instrument_rejected(self):
        instrument = Instrument.create(
            symbol="BTC-USDT",
            base_asset="BTC",
            quote_asset="USDT",
            tick_size=0.01,
            lot_size=0.001,
        )
        with pytest.raises(ValueError, match="must not contain"):
            OrderIntent(
                intent_type=IntentType.NO_ACTION,
                instrument=instrument,
            )


class TestBalance:
    def test_valid(self):
        b = Balance(available=100.0, locked=50.0, total=150.0)
        assert b.total == 150.0

    def test_inconsistent_total(self):
        with pytest.raises(ValueError, match="total"):
            Balance(available=100.0, locked=50.0, total=200.0)

    def test_negative_available(self):
        with pytest.raises(ValueError, match="available"):
            Balance(available=-10.0, locked=0.0, total=-10.0)

    def test_negative_locked(self):
        with pytest.raises(ValueError, match="locked"):
            Balance(available=10.0, locked=-5.0, total=5.0)

    def test_zero_balance(self):
        b = Balance(available=0.0, locked=0.0, total=0.0)
        assert b.total == 0.0


class TestTimeRange:
    def test_valid(self, utc_now):
        tr = TimeRange(
            start=utc_now,
            end=utc_now + timedelta(hours=1),
        )
        assert tr.start < tr.end

    def test_start_after_end_rejected(self, utc_now):
        with pytest.raises(ValueError, match=r"start.*before.*end"):
            TimeRange(
                start=utc_now + timedelta(hours=1),
                end=utc_now,
            )

    def test_equal_start_end_rejected(self, utc_now):
        with pytest.raises(ValueError, match=r"start.*before.*end"):
            TimeRange(start=utc_now, end=utc_now)

    def test_naive_start_rejected(self, utc_now):
        with pytest.raises(ValueError, match="timezone"):
            TimeRange(start=datetime(2024, 1, 1), end=utc_now)

    def test_naive_end_rejected(self, utc_now):
        with pytest.raises(ValueError, match="timezone"):
            TimeRange(start=utc_now, end=datetime(2025, 1, 1))


class TestMarketEvent:
    def test_valid_event(self, utc_now):
        event = MarketEvent.create(
            event_type=MarketEventType.BAR,
            timestamp=utc_now,
            symbol="BTC-USDT",
            payload={"price": 50000.0},
        )
        assert isinstance(event.payload, MappingProxyType)

    def test_payload_immutable(self, utc_now):
        event = MarketEvent.create(
            event_type=MarketEventType.TRADE,
            timestamp=utc_now,
            symbol="BTC-USDT",
            payload={"key": "value"},
        )
        with pytest.raises(TypeError):
            event.payload["new"] = "data"  # type: ignore[index]

    def test_naive_timestamp_rejected(self):
        with pytest.raises(ValueError, match="timezone"):
            MarketEvent.create(
                event_type=MarketEventType.BAR,
                timestamp=datetime(2024, 1, 1),
                symbol="BTC-USDT",
            )


class TestStrategyContext:
    def test_valid_context(self, utc_now):
        ctx = StrategyContext.create(
            timestamp=utc_now,
            balance_available=1000.0,
            balance_locked=0.0,
            parameters={"param_a": 0.5},
        )
        assert isinstance(ctx.parameters, MappingProxyType)

    def test_parameters_immutable(self, utc_now):
        ctx = StrategyContext.create(
            timestamp=utc_now,
            balance_available=1000.0,
            balance_locked=0.0,
            parameters={"key": "val"},
        )
        with pytest.raises(TypeError):
            ctx.parameters["new"] = "x"  # type: ignore[index]

    def test_negative_balance_rejected(self, utc_now):
        with pytest.raises(ValueError, match="balance_available"):
            StrategyContext.create(
                timestamp=utc_now,
                balance_available=-100.0,
                balance_locked=0.0,
            )


class TestSimulationResult:
    def test_valid(self, utc_now):
        sr = SimulationResult.create(
            experiment_id="exp-001",
            timestamp=utc_now,
            metadata={"key": "value"},
            events_log=[{"event": "fill", "qty": 1.0}],
        )
        assert isinstance(sr.metadata, MappingProxyType)
        assert isinstance(sr.events_log, tuple)
        assert isinstance(sr.events_log[0], MappingProxyType)

    def test_metadata_immutable(self, utc_now):
        sr = SimulationResult.create(
            experiment_id="exp-001",
            timestamp=utc_now,
            metadata={"key": "value"},
        )
        with pytest.raises(TypeError):
            sr.metadata["new"] = "val"  # type: ignore[index]

    def test_events_log_immutable(self, utc_now):
        sr = SimulationResult.create(
            experiment_id="exp-001",
            timestamp=utc_now,
            events_log=[{"a": 1}],
        )
        with pytest.raises(TypeError):
            sr.events_log[0]["b"] = 2  # type: ignore[index]

    def test_empty_experiment_id_rejected(self, utc_now):
        with pytest.raises(ValueError, match="experiment_id"):
            SimulationResult.create(experiment_id="", timestamp=utc_now)


class TestMetricsResult:
    def test_valid(self, utc_now):
        mr = MetricsResult.create(
            experiment_id="exp-001",
            timestamp=utc_now,
            metrics={"sharpe": 1.5},
            benchmarks={"baseline": 0.8},
        )
        assert mr.metrics["sharpe"] == 1.5

    def test_metrics_immutable(self, utc_now):
        mr = MetricsResult.create(
            experiment_id="exp-001",
            timestamp=utc_now,
            metrics={"key": "val"},
        )
        with pytest.raises(TypeError):
            mr.metrics["new"] = "x"  # type: ignore[index]

    def test_benchmarks_immutable(self, utc_now):
        mr = MetricsResult.create(
            experiment_id="exp-001",
            timestamp=utc_now,
            benchmarks={"bench": 1.0},
        )
        with pytest.raises(TypeError):
            mr.benchmarks["new"] = "x"  # type: ignore[index]
