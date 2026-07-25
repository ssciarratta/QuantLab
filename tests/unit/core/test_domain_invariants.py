"""Tests profundos de invariantes de dominio (Fase 2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ManifestError, ValidationError
from quantlab.core.types import (
    Balance,
    Bar,
    BookLevel,
    DatasetManifest,
    ExecutionModelVersions,
    ExperimentManifest,
    Fee,
    Fill,
    Instrument,
    Order,
    OrderIntent,
    TimeRange,
    Trade,
)
from quantlab.core.types.enums import (
    FeeType,
    IntentType,
    LiquidityType,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)


def _ts(year: int = 2024, month: int = 1, day: int = 1) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def _instrument(**overrides: object) -> Instrument:
    data: dict[str, object] = {
        "instrument_id": "id-1",
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "venue_id": "binance",
        "tick_size": Decimal("0.01"),
        "lot_size": Decimal("0.0001"),
        "min_notional": Decimal("10"),
    }
    data.update(overrides)
    return Instrument(**data)  # type: ignore[arg-type]


# --- Instrument ---


def test_instrument_valid() -> None:
    inst = _instrument(metadata={"a": 1})
    assert inst.symbol == "BTCUSDT"
    with pytest.raises(TypeError):
        inst.metadata["a"] = 2  # type: ignore[index]


def test_instrument_rejects_empty_symbol() -> None:
    with pytest.raises(ValidationError):
        _instrument(symbol="")


def test_instrument_rejects_same_base_quote() -> None:
    with pytest.raises(ValidationError):
        _instrument(base_asset="BTC", quote_asset="BTC")


def test_instrument_rejects_non_positive_sizes() -> None:
    with pytest.raises(ValidationError):
        _instrument(tick_size=Decimal("0"))
    with pytest.raises(ValidationError):
        _instrument(lot_size=Decimal("-1"))
    with pytest.raises(ValidationError):
        _instrument(min_notional=Decimal("0"))


# --- TimeRange ---


def test_time_range_valid_and_timezone() -> None:
    ar = timezone(timedelta(hours=-3))
    start = datetime(2024, 1, 1, tzinfo=ar)
    end = datetime(2024, 1, 2, tzinfo=ar)
    tr = TimeRange(start=start, end=end)
    assert tr.end > tr.start


def test_time_range_rejects_order_and_naive() -> None:
    with pytest.raises(ValidationError):
        TimeRange(start=_ts(day=2), end=_ts(day=1))
    with pytest.raises(ValidationError):
        TimeRange(start=datetime(2024, 1, 1), end=_ts(day=2))
    with pytest.raises(ValidationError):
        TimeRange(start=_ts(), end=datetime(2024, 1, 2))


# --- Bar ---


def test_bar_valid() -> None:
    bar = Bar(
        instrument_id="x",
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal("105"),
        volume=Decimal("1"),
        timestamp_open=_ts(),
        timestamp_close=_ts(day=1),
        timeframe="1m",
    )
    assert bar.high >= bar.open


def test_bar_rejects_bad_ohlc_and_volume() -> None:
    base = {
        "instrument_id": "x",
        "open": Decimal("100"),
        "high": Decimal("110"),
        "low": Decimal("90"),
        "close": Decimal("105"),
        "volume": Decimal("1"),
        "timestamp_open": _ts(),
        "timestamp_close": datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
        "timeframe": "1m",
    }
    with pytest.raises(ValidationError):
        Bar(**{**base, "open": Decimal("0")})  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Bar(**{**base, "high": Decimal("80")})  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Bar(**{**base, "low": Decimal("120")})  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Bar(**{**base, "volume": Decimal("-1")})  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Bar(**{**base, "timestamp_open": datetime(2024, 1, 1)})  # type: ignore[arg-type]


# --- BookLevel / Trade / Fill ---


def test_book_level_rules() -> None:
    assert BookLevel(price=Decimal("1"), quantity=Decimal("0")).quantity == 0
    with pytest.raises(ValidationError):
        BookLevel(price=Decimal("0"), quantity=Decimal("1"))
    with pytest.raises(ValidationError):
        BookLevel(price=Decimal("1"), quantity=Decimal("-1"))


def test_trade_and_fill_rules() -> None:
    trade = Trade(
        instrument_id="x",
        price=Decimal("10"),
        quantity=Decimal("1"),
        side=OrderSide.BUY,
        timestamp=_ts(),
        trade_id="t1",
    )
    assert trade.price > 0
    with pytest.raises(ValidationError):
        Trade(
            instrument_id="x",
            price=Decimal("0"),
            quantity=Decimal("1"),
            side=OrderSide.BUY,
            timestamp=_ts(),
            trade_id="t1",
        )
    with pytest.raises(ValidationError):
        Trade(
            instrument_id="x",
            price=Decimal("1"),
            quantity=Decimal("0"),
            side=OrderSide.BUY,
            timestamp=_ts(),
            trade_id="t1",
        )
    with pytest.raises(ValidationError):
        Trade(
            instrument_id="x",
            price=Decimal("1"),
            quantity=Decimal("1"),
            side=OrderSide.BUY,
            timestamp=datetime(2024, 1, 1),
            trade_id="t1",
        )

    fee = Fee(
        fee_id="f1",
        fill_id="fill1",
        amount=Decimal("0.1"),
        currency="USDT",
        fee_type=FeeType.TAKER,
    )
    fill = Fill(
        fill_id="fill1",
        order_id="o1",
        instrument_id="x",
        price=Decimal("10"),
        quantity=Decimal("1"),
        fee=fee,
        timestamp=_ts(),
        liquidity=LiquidityType.TAKER,
    )
    assert fill.quantity > 0
    with pytest.raises(ValidationError):
        Fill(
            fill_id="fill1",
            order_id="o1",
            instrument_id="x",
            price=Decimal("-1"),
            quantity=Decimal("1"),
            fee=fee,
            timestamp=_ts(),
            liquidity=LiquidityType.TAKER,
        )


# --- Order ---


def test_order_valid_and_invalid() -> None:
    order = Order(
        order_id="o1",
        client_order_id="c1",
        instrument_id="x",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1"),
        filled_quantity=Decimal("0.5"),
        price=Decimal("100"),
        status=OrderStatus.PARTIAL,
        created_at=_ts(),
        updated_at=_ts(),
        time_in_force=TimeInForce.GTC,
    )
    assert order.filled_quantity <= order.quantity

    with pytest.raises(ValidationError):
        Order(
            order_id="o1",
            client_order_id="c1",
            instrument_id="x",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0"),
            filled_quantity=Decimal("0"),
            price=Decimal("100"),
            status=OrderStatus.OPEN,
            created_at=_ts(),
            updated_at=_ts(),
            time_in_force=TimeInForce.GTC,
        )
    with pytest.raises(ValidationError):
        Order(
            order_id="o1",
            client_order_id="c1",
            instrument_id="x",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1"),
            filled_quantity=Decimal("-1"),
            price=Decimal("100"),
            status=OrderStatus.OPEN,
            created_at=_ts(),
            updated_at=_ts(),
            time_in_force=TimeInForce.GTC,
        )
    with pytest.raises(ValidationError):
        Order(
            order_id="o1",
            client_order_id="c1",
            instrument_id="x",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1"),
            filled_quantity=Decimal("2"),
            price=Decimal("100"),
            status=OrderStatus.OPEN,
            created_at=_ts(),
            updated_at=_ts(),
            time_in_force=TimeInForce.GTC,
        )
    with pytest.raises(ValidationError):
        Order(
            order_id="o1",
            client_order_id="c1",
            instrument_id="x",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1"),
            filled_quantity=Decimal("0"),
            price=None,
            status=OrderStatus.OPEN,
            created_at=_ts(),
            updated_at=_ts(),
            time_in_force=TimeInForce.GTC,
        )
    with pytest.raises(ValidationError):
        Order(
            order_id="o1",
            client_order_id="c1",
            instrument_id="x",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1"),
            filled_quantity=Decimal("0"),
            price=Decimal("100"),
            status=OrderStatus.OPEN,
            created_at=_ts(),
            updated_at=_ts(),
        )


# --- Balance ---


def test_balance_coherence_and_precision() -> None:
    bal = Balance(
        asset="USDT",
        available=Decimal("10.50"),
        locked=Decimal("1.25"),
        total=Decimal("11.75"),
        updated_at=_ts(),
    )
    assert bal.available + bal.locked == bal.total
    with pytest.raises(ValidationError):
        Balance(
            asset="USDT",
            available=Decimal("-1"),
            locked=Decimal("0"),
            total=Decimal("0"),
            updated_at=_ts(),
        )
    with pytest.raises(ValidationError):
        Balance(
            asset="USDT",
            available=Decimal("1"),
            locked=Decimal("1"),
            total=Decimal("3"),
            updated_at=_ts(),
        )


# --- OrderIntent ---


def test_order_intent_place_cancel_replace_no_action() -> None:
    place = OrderIntent(
        intent_id="i1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="x",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("10"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    assert place.intent_type is IntentType.PLACE_ORDER

    cancel = OrderIntent(
        intent_id="i2",
        intent_type=IntentType.CANCEL_ORDER,
        instrument_id="x",
        replace_target_id="o1",
    )
    assert cancel.replace_target_id == "o1"

    replace = OrderIntent(
        intent_id="i3",
        intent_type=IntentType.REPLACE_ORDER,
        instrument_id="x",
        side=OrderSide.SELL,
        quantity=Decimal("2"),
        price=Decimal("11"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.IOC,
        replace_target_id="o1",
    )
    assert replace.replace_target_id == "o1"

    no_action = OrderIntent(
        intent_id="i4",
        intent_type=IntentType.NO_ACTION,
        instrument_id="x",
    )
    assert no_action.side is None

    with pytest.raises(ValidationError):
        OrderIntent(
            intent_id="bad",
            intent_type=IntentType.PLACE_ORDER,
            instrument_id="x",
            side=OrderSide.BUY,
            quantity=Decimal("0"),
            price=Decimal("10"),
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
        )
    with pytest.raises(ValidationError):
        OrderIntent(
            intent_id="bad",
            intent_type=IntentType.CANCEL_ORDER,
            instrument_id="x",
        )
    with pytest.raises(ValidationError):
        OrderIntent(
            intent_id="bad",
            intent_type=IntentType.NO_ACTION,
            instrument_id="x",
            side=OrderSide.BUY,
        )
    with pytest.raises(ValidationError):
        OrderIntent(
            intent_id="bad",
            intent_type=IntentType.PLACE_ORDER,
            instrument_id="x",
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            order_type=OrderType.MARKET,
            price=Decimal("1"),
        )
    with pytest.raises(AttributeError):
        place.quantity = Decimal("9")  # type: ignore[misc]


# --- Manifests ---


def test_manifests_validation_and_deterministic_serialization() -> None:
    tr = TimeRange(start=_ts(), end=_ts(day=2))
    ds = DatasetManifest(
        dataset_id="ds1",
        version="v1",
        source="test",
        instruments=("a",),
        time_range=tr,
        granularity="1m",
        schema_version="1.0",
        checksum="a" * 64,
        row_count=1,
        storage_path="/tmp/x",
        created_at=_ts(),
    )
    d1 = ds.to_dict()
    d2 = ds.to_dict()
    assert d1 == d2

    with pytest.raises(ManifestError):
        DatasetManifest(
            dataset_id="",
            version="v1",
            source="test",
            instruments=("a",),
            time_range=tr,
            granularity="1m",
            schema_version="1.0",
            checksum="a" * 64,
            row_count=1,
            storage_path="/tmp/x",
            created_at=_ts(),
        )
    with pytest.raises(ManifestError):
        DatasetManifest(
            dataset_id="ds1",
            version="v1",
            source="test",
            instruments=("a",),
            time_range=tr,
            granularity="1m",
            schema_version="latest",
            checksum="a" * 64,
            row_count=1,
            storage_path="/tmp/x",
            created_at=_ts(),
        )
    with pytest.raises(ManifestError):
        DatasetManifest(
            dataset_id="ds1",
            version="v1",
            source="test",
            instruments=("a",),
            time_range=tr,
            granularity="1m",
            schema_version="1.0",
            checksum="zzz",
            row_count=1,
            storage_path="/tmp/x",
            created_at=_ts(),
        )
    with pytest.raises(ValidationError):
        DatasetManifest(
            dataset_id="ds1",
            version="v1",
            source="test",
            instruments=("a",),
            time_range=tr,
            granularity="1m",
            schema_version="1.0",
            checksum="a" * 64,
            row_count=1,
            storage_path="/tmp/x",
            created_at=datetime(2024, 1, 1),
        )

    models = ExecutionModelVersions(
        fee_model="n",
        slippage_model="n",
        latency_model="n",
        fill_model="n",
    )
    exp = ExperimentManifest(
        experiment_id="e1",
        dataset_id="ds1",
        dataset_version="v1",
        resolved_config={"b": 2, "a": 1},
        seed=0,
        git_commit="abc",
        python_version="3.12.0",
        dependency_versions_or_hash="deadbeef",
        platform="test",
        strategy_version="0.0.1",
        execution_model_versions=models,
        artifacts_produced=(),
        created_at=_ts(),
        checksum="b" * 64,
    )
    with pytest.raises(TypeError):
        exp.resolved_config["a"] = 99  # type: ignore[index]
    ser = exp.to_dict()
    assert list(ser["resolved_config"].keys()) == ["a", "b"]

    with pytest.raises(ManifestError):
        ExperimentManifest(
            experiment_id="e1",
            dataset_id="ds1",
            dataset_version="v1",
            resolved_config={},
            seed=-1,
            git_commit="abc",
            python_version="3.12.0",
            dependency_versions_or_hash="deadbeef",
            platform="test",
            strategy_version="0.0.1",
            execution_model_versions=models,
            artifacts_produced=(),
            created_at=_ts(),
            checksum="b" * 64,
        )
    with pytest.raises(ManifestError):
        ExperimentManifest(
            experiment_id="e1",
            dataset_id="ds1",
            dataset_version="v1",
            resolved_config={},
            seed=1,
            git_commit="",
            python_version="3.12.0",
            dependency_versions_or_hash="deadbeef",
            platform="test",
            strategy_version="0.0.1",
            execution_model_versions=models,
            artifacts_produced=(),
            created_at=_ts(),
            checksum="b" * 64,
        )
    with pytest.raises(ManifestError):
        ExperimentManifest(
            experiment_id="e1",
            dataset_id="ds1",
            dataset_version="v1",
            resolved_config={},
            seed=1,
            git_commit="abc",
            python_version="3.12.0",
            dependency_versions_or_hash="",
            platform="test",
            strategy_version="0.0.1",
            execution_model_versions=models,
            artifacts_produced=(),
            created_at=_ts(),
            checksum="b" * 64,
        )
    with pytest.raises(ManifestError):
        ExperimentManifest(
            experiment_id="e1",
            dataset_id="ds1",
            dataset_version="v1",
            resolved_config={},
            seed=1,
            git_commit="abc",
            python_version="3.12.0",
            dependency_versions_or_hash="deadbeef",
            platform="test",
            strategy_version="0.0.1",
            execution_model_versions=models,
            artifacts_produced=(),
            created_at=_ts(),
            checksum="short",
        )
    with pytest.raises(ManifestError):
        DatasetManifest(
            dataset_id="ds1",
            version="v1",
            source="test",
            instruments=(),
            time_range=tr,
            granularity="1m",
            schema_version="1.0",
            checksum="a" * 64,
            row_count=1,
            storage_path="/tmp/x",
            created_at=_ts(),
        )


def test_timezone_utc_accepted() -> None:
    tr = TimeRange(start=datetime(2024, 1, 1, tzinfo=UTC), end=_ts(day=2))
    assert tr.start.tzinfo is not None
