"""Tests offline Data Layer + A3 (sin credenciales)."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.orders import OrderIntent
from quantlab.data.exchanges.a3.adapter import A3Adapter
from quantlab.data.exchanges.a3.config import A3Config, load_a3_config
from quantlab.data.exchanges.a3.constants import LIVE_TRADING_CONFIRMATION, A3EnvironmentName
from quantlab.data.exchanges.a3.exceptions import (
    A3LiveTradingDisabledError,
    A3RiskRejectedError,
)
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend
from quantlab.data.exchanges.a3.kill_switch import KillSwitch, KillSwitchState
from quantlab.data.exchanges.a3.mappers import parse_instrument_dto, sanitize_symbol_for_path
from quantlab.data.normalization.bars import build_bars_from_trades
from quantlab.data.quality.validators import validate_trades


def _adapter(tmp_path: Path, *, production: bool = False) -> A3Adapter:
    root = Path.cwd()
    cfg = load_a3_config(root / "config" / "exchanges" / "a3.yaml")
    # Override storage to tmp
    storage = cfg.storage.__class__(
        raw_root=tmp_path / "raw",
        processed_root=tmp_path / "processed",
        catalog_path=tmp_path / "catalog.sqlite",
        kill_switch_path=tmp_path / "kill.json",
    )
    env = A3EnvironmentName.PRODUCTION if production else A3EnvironmentName.SIMULATION
    cfg2 = A3Config(
        enabled=True,
        environment=env,
        market_data=cfg.market_data,
        execution=cfg.execution.__class__(
            enabled=True,
            allow_live_orders=False,
            account_allowlist=(),
            require_live_confirmation=True,
        ),
        storage=storage,
        risk=cfg.risk,
    )
    adapter = A3Adapter(cfg2, FakeA3Backend(), account="SIM-001")
    adapter.connect()
    return adapter


def test_sanitize_symbol() -> None:
    assert sanitize_symbol_for_path("DLR/DIC24") == "DLR_DIC24"


def test_slice_a_instruments(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    instruments = adapter.get_instruments()
    assert instruments
    assert instruments[0].venue_id == "a3"
    assert (tmp_path / "raw").exists()


def test_slice_b_historical_bars(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    end = datetime(2024, 6, 3, 16, tzinfo=UTC)
    start = end - timedelta(days=1)
    bars, manifest = adapter.get_historical_bars("DLR/DIC24", "1m", start, end)
    assert len(bars) >= 1
    assert manifest.schema_version == "1.0"
    assert adapter.catalog.verify_dataset(manifest.dataset_id)


def test_slice_c_websocket_queue(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    handler = adapter.subscribe_market_data(["DLR/DIC24"]).handler
    for _ in range(3):
        handler({"BI": [{"price": "1", "size": "1"}]})
    items = adapter.websocket_capture.drain()
    assert len(items) == 3
    assert adapter.websocket_capture.stats.dropped == 0


def test_slice_d_simulation_order_and_cancel(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    adapter.get_market_snapshot("DLR/DIC24")
    intent = OrderIntent(
        intent_id="test-intent-1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="a3:DLR/DIC24",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("1000"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    ack = adapter.place_order(intent)
    assert ack.order_id
    canceled = adapter.cancel_order(ack.order_id)
    assert canceled.status == "CANCELED"


def test_production_orders_blocked_even_with_fake_creds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QUANTLAB_ENABLE_LIVE_TRADING", "DISABLED")
    adapter = _adapter(tmp_path, production=True)
    adapter.get_market_snapshot("DLR/DIC24")
    intent = OrderIntent(
        intent_id="live-blocked",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="a3:DLR/DIC24",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("1000"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    with pytest.raises(A3LiveTradingDisabledError):
        adapter.place_order(intent)


def test_kill_switch_blocks(tmp_path: Path) -> None:
    path = tmp_path / "kill.json"
    ks = KillSwitch(path)
    ks.save(KillSwitchState(block_all_orders=True, block_production=True))
    blocked, scope = ks.is_blocked(is_production=False, account="x", symbol="y")
    assert blocked and scope == "all_orders"


def test_bars_from_trades_deterministic() -> None:
    from quantlab.core.types.market import Trade

    t0 = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    trades = [
        Trade(
            instrument_id="a3:X",
            price=Decimal("10"),
            quantity=Decimal("1"),
            side=OrderSide.BUY,
            timestamp=t0,
            trade_id="1",
        ),
        Trade(
            instrument_id="a3:X",
            price=Decimal("11"),
            quantity=Decimal("1"),
            side=OrderSide.SELL,
            timestamp=t0 + timedelta(seconds=10),
            trade_id="2",
        ),
        Trade(
            instrument_id="a3:X",
            price=Decimal("11"),
            quantity=Decimal("1"),
            side=OrderSide.SELL,
            timestamp=t0 + timedelta(seconds=10),
            trade_id="2",
        ),
    ]
    report = build_bars_from_trades(trades, timeframe="1m", instrument_id="a3:X")
    assert report.duplicate_trades_removed == 1
    assert len(report.bars) == 1
    assert report.bars[0].open == Decimal("10")
    assert report.bars[0].high == Decimal("11")


def test_parse_instrument_and_quality() -> None:
    dto = parse_instrument_dto(
        {
            "symbol": "ABC",
            "tickIncrement": "0.01",
            "minLotSize": "1",
            "currency": "ARS",
            "underlying": "XYZ",
        }
    )
    assert dto.symbol == "ABC"
    # quality empty list ok
    assert validate_trades([]).issues == ()


def test_risk_rejects_oversized(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    adapter.get_market_snapshot("DLR/DIC24")
    intent = OrderIntent(
        intent_id="big",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="a3:DLR/DIC24",
        side=OrderSide.BUY,
        quantity=Decimal("100"),
        price=Decimal("1000"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    with pytest.raises(A3RiskRejectedError):
        adapter.place_order(intent)


def test_live_confirmation_constant_not_default() -> None:
    assert os.environ.get("QUANTLAB_ENABLE_LIVE_TRADING", "DISABLED") != LIVE_TRADING_CONFIRMATION
