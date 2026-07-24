"""Tests for market domain types — invariants and immutability."""

from __future__ import annotations

from datetime import datetime
from types import MappingProxyType

import pytest

from quantlab.core.types.market import (
    Bar,
    BookLevel,
    Fill,
    Instrument,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Trade,
)


class TestInstrument:
    def test_valid_instrument(self, sample_instrument):
        assert sample_instrument.symbol == "BTC-USDT"
        assert sample_instrument.tick_size == 0.01

    def test_empty_symbol_rejected(self):
        with pytest.raises(ValueError, match="symbol"):
            Instrument.create(
                symbol="",
                base_asset="BTC",
                quote_asset="USDT",
                tick_size=0.01,
                lot_size=0.001,
            )

    def test_whitespace_symbol_rejected(self):
        with pytest.raises(ValueError, match="symbol"):
            Instrument.create(
                symbol="   ",
                base_asset="BTC",
                quote_asset="USDT",
                tick_size=0.01,
                lot_size=0.001,
            )

    def test_negative_tick_size_rejected(self):
        with pytest.raises(ValueError, match="tick_size"):
            Instrument.create(
                symbol="BTC-USDT",
                base_asset="BTC",
                quote_asset="USDT",
                tick_size=-0.01,
                lot_size=0.001,
            )

    def test_zero_tick_size_rejected(self):
        with pytest.raises(ValueError, match="tick_size"):
            Instrument.create(
                symbol="BTC-USDT",
                base_asset="BTC",
                quote_asset="USDT",
                tick_size=0,
                lot_size=0.001,
            )

    def test_zero_lot_size_rejected(self):
        with pytest.raises(ValueError, match="lot_size"):
            Instrument.create(
                symbol="BTC-USDT",
                base_asset="BTC",
                quote_asset="USDT",
                tick_size=0.01,
                lot_size=0,
            )

    def test_negative_min_notional_rejected(self):
        with pytest.raises(ValueError, match="min_notional"):
            Instrument.create(
                symbol="BTC-USDT",
                base_asset="BTC",
                quote_asset="USDT",
                tick_size=0.01,
                lot_size=0.001,
                min_notional=-1.0,
            )

    def test_same_base_quote_rejected(self):
        with pytest.raises(ValueError, match="must differ"):
            Instrument.create(
                symbol="BTC-BTC",
                base_asset="BTC",
                quote_asset="BTC",
                tick_size=0.01,
                lot_size=0.001,
            )

    def test_metadata_is_immutable(self, sample_instrument):
        assert isinstance(sample_instrument.metadata, MappingProxyType)
        with pytest.raises(TypeError):
            sample_instrument.metadata["new_key"] = "value"  # type: ignore[index]

    def test_frozen_dataclass(self, sample_instrument):
        with pytest.raises(AttributeError):
            sample_instrument.symbol = "ETH-USDT"


class TestBar:
    def test_valid_bar(self, utc_now):
        bar = Bar(
            timestamp=utc_now,
            open=100.0,
            high=110.0,
            low=95.0,
            close=105.0,
            volume=1000.0,
            symbol="BTC-USDT",
        )
        assert bar.high == 110.0

    def test_naive_timestamp_rejected(self):
        with pytest.raises(ValueError, match="timezone"):
            Bar(
                timestamp=datetime(2024, 1, 1),
                open=100.0,
                high=110.0,
                low=95.0,
                close=105.0,
                volume=1000.0,
                symbol="BTC-USDT",
            )

    def test_high_less_than_open_rejected(self, utc_now):
        with pytest.raises(ValueError, match=r"high.*open"):
            Bar(
                timestamp=utc_now,
                open=110.0,
                high=100.0,
                low=95.0,
                close=105.0,
                volume=1000.0,
                symbol="BTC-USDT",
            )

    def test_high_less_than_close_rejected(self, utc_now):
        with pytest.raises(ValueError, match=r"high.*close"):
            Bar(
                timestamp=utc_now,
                open=100.0,
                high=103.0,
                low=95.0,
                close=105.0,
                volume=1000.0,
                symbol="BTC-USDT",
            )

    def test_high_less_than_low_rejected(self, utc_now):
        with pytest.raises(ValueError, match=r"high.*low"):
            Bar(
                timestamp=utc_now,
                open=90.0,
                high=94.0,
                low=95.0,
                close=90.0,
                volume=1000.0,
                symbol="BTC-USDT",
            )

    def test_low_greater_than_open_rejected(self, utc_now):
        with pytest.raises(ValueError, match=r"low.*open"):
            Bar(
                timestamp=utc_now,
                open=100.0,
                high=110.0,
                low=105.0,
                close=106.0,
                volume=1000.0,
                symbol="BTC-USDT",
            )

    def test_low_greater_than_close_rejected(self, utc_now):
        with pytest.raises(ValueError, match=r"low.*close"):
            Bar(
                timestamp=utc_now,
                open=105.0,
                high=110.0,
                low=104.0,
                close=103.0,
                volume=1000.0,
                symbol="BTC-USDT",
            )

    def test_negative_volume_rejected(self, utc_now):
        with pytest.raises(ValueError, match="volume"):
            Bar(
                timestamp=utc_now,
                open=100.0,
                high=110.0,
                low=95.0,
                close=105.0,
                volume=-1.0,
                symbol="BTC-USDT",
            )

    def test_zero_price_rejected(self, utc_now):
        with pytest.raises(ValueError, match="open"):
            Bar(
                timestamp=utc_now,
                open=0.0,
                high=110.0,
                low=95.0,
                close=105.0,
                volume=1000.0,
                symbol="BTC-USDT",
            )

    def test_negative_price_rejected(self, utc_now):
        with pytest.raises(ValueError, match="open"):
            Bar(
                timestamp=utc_now,
                open=-5.0,
                high=110.0,
                low=95.0,
                close=105.0,
                volume=1000.0,
                symbol="BTC-USDT",
            )

    def test_empty_symbol_rejected(self, utc_now):
        with pytest.raises(ValueError, match="symbol"):
            Bar(
                timestamp=utc_now,
                open=100.0,
                high=110.0,
                low=95.0,
                close=105.0,
                volume=1000.0,
                symbol="",
            )

    def test_zero_volume_allowed(self, utc_now):
        bar = Bar(
            timestamp=utc_now,
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=0.0,
            symbol="BTC-USDT",
        )
        assert bar.volume == 0.0

    def test_equal_ohlc_allowed(self, utc_now):
        bar = Bar(
            timestamp=utc_now,
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=100.0,
            symbol="BTC-USDT",
        )
        assert bar.open == bar.close == bar.high == bar.low


class TestBookLevel:
    def test_valid(self):
        bl = BookLevel(price=100.0, quantity=10.0)
        assert bl.price == 100.0

    def test_zero_price_rejected(self):
        with pytest.raises(ValueError, match="price"):
            BookLevel(price=0.0, quantity=10.0)

    def test_negative_quantity_rejected(self):
        with pytest.raises(ValueError, match="quantity"):
            BookLevel(price=100.0, quantity=-1.0)

    def test_zero_quantity_allowed(self):
        bl = BookLevel(price=100.0, quantity=0.0)
        assert bl.quantity == 0.0


class TestTrade:
    def test_valid(self, utc_now):
        t = Trade(
            symbol="BTC-USDT",
            price=50000.0,
            quantity=0.5,
            timestamp=utc_now,
            side=OrderSide.BUY,
        )
        assert t.price == 50000.0

    def test_zero_price_rejected(self, utc_now):
        with pytest.raises(ValueError, match="price"):
            Trade(
                symbol="BTC-USDT",
                price=0.0,
                quantity=0.5,
                timestamp=utc_now,
                side=OrderSide.BUY,
            )

    def test_zero_quantity_rejected(self, utc_now):
        with pytest.raises(ValueError, match="quantity"):
            Trade(
                symbol="BTC-USDT",
                price=50000.0,
                quantity=0.0,
                timestamp=utc_now,
                side=OrderSide.BUY,
            )

    def test_naive_timestamp_rejected(self):
        with pytest.raises(ValueError, match="timezone"):
            Trade(
                symbol="BTC-USDT",
                price=50000.0,
                quantity=0.5,
                timestamp=datetime(2024, 1, 1),
                side=OrderSide.BUY,
            )


class TestFill:
    def test_valid(self, utc_now):
        f = Fill(
            order_id="ord-1",
            price=50000.0,
            quantity=0.5,
            timestamp=utc_now,
            side=OrderSide.BUY,
            fee=2.5,
        )
        assert f.fee == 2.5

    def test_empty_order_id_rejected(self, utc_now):
        with pytest.raises(ValueError, match="order_id"):
            Fill(
                order_id="",
                price=50000.0,
                quantity=0.5,
                timestamp=utc_now,
                side=OrderSide.BUY,
            )

    def test_negative_fee_rejected(self, utc_now):
        with pytest.raises(ValueError, match="fee"):
            Fill(
                order_id="ord-1",
                price=50000.0,
                quantity=0.5,
                timestamp=utc_now,
                side=OrderSide.BUY,
                fee=-1.0,
            )


class TestOrder:
    def test_valid_limit_order(self, utc_now):
        o = Order(
            order_id="ord-1",
            symbol="BTC-USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0,
            timestamp=utc_now,
        )
        assert o.status == OrderStatus.PENDING

    def test_limit_without_price_rejected(self, utc_now):
        with pytest.raises(ValueError, match=r"LIMIT.*price"):
            Order(
                order_id="ord-1",
                symbol="BTC-USDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=1.0,
                timestamp=utc_now,
            )

    def test_filled_greater_than_quantity_rejected(self, utc_now):
        with pytest.raises(ValueError, match="filled_quantity"):
            Order(
                order_id="ord-1",
                symbol="BTC-USDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1.0,
                filled_quantity=2.0,
                timestamp=utc_now,
            )

    def test_zero_quantity_rejected(self, utc_now):
        with pytest.raises(ValueError, match="quantity"):
            Order(
                order_id="ord-1",
                symbol="BTC-USDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.0,
                timestamp=utc_now,
            )

    def test_negative_filled_quantity_rejected(self, utc_now):
        with pytest.raises(ValueError, match="filled_quantity"):
            Order(
                order_id="ord-1",
                symbol="BTC-USDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=1.0,
                filled_quantity=-0.5,
                timestamp=utc_now,
            )

    def test_market_order_valid(self, utc_now):
        o = Order(
            order_id="ord-1",
            symbol="BTC-USDT",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=1.0,
            timestamp=utc_now,
        )
        assert o.price is None
