"""Cobertura offline de mappers, risk, catalog y replay A3."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.manifests import DatasetManifest, TimeRange
from quantlab.core.types.orders import OrderIntent
from quantlab.data.catalog.catalog import DataCatalog
from quantlab.data.exchanges.a3.config import A3Config, load_a3_config
from quantlab.data.exchanges.a3.constants import A3EnvironmentName
from quantlab.data.exchanges.a3.exceptions import A3MappingError
from quantlab.data.exchanges.a3.kill_switch import KillSwitch, KillSwitchState
from quantlab.data.exchanges.a3.mappers import (
    A3SymbolMapper,
    book_levels_to_domain,
    instrument_dto_to_domain,
    parse_instrument_dto,
    parse_snapshot_dto,
    parse_trade_dto,
    trade_dto_to_domain,
)
from quantlab.data.exchanges.a3.models import A3BookLevelDTO
from quantlab.data.exchanges.a3.persistence import ProcessedStore, RawStore
from quantlab.data.exchanges.a3.risk import DefaultPreTradeRiskGate, TradingContext
from quantlab.data.exchanges.a3.validation import validate_bars, validate_trades
from quantlab.data.quality.validators import validate_bars as vb
from quantlab.data.replay import load_catalog_entry


def test_mapper_errors_and_snapshot() -> None:
    mapper = A3SymbolMapper()
    assert mapper.normalize(" abc ") == "ABC"
    assert mapper.to_path_safe("a/b") == "A_B"

    with pytest.raises(A3MappingError):
        parse_instrument_dto({})
    with pytest.raises(A3MappingError):
        parse_trade_dto("X", {"price": "1"})
    with pytest.raises(A3MappingError):
        parse_trade_dto("X", {"price": "bad", "size": "1", "timestamp": "2024-01-01T00:00:00Z"})

    dto = parse_instrument_dto(
        {
            "symbol": "FOO/BAR",
            "securityStatus": "SUSPENDED",
            "currency": "USD",
            "underlying": "USD",
        }
    )
    inst = instrument_dto_to_domain(dto)
    assert inst.status.name == "DELISTED"
    assert inst.quote_asset == "ARS"

    trade = parse_trade_dto(
        "X",
        {
            "Px": "10",
            "LastQty": "2",
            "datetime": 1_700_000_000,
            "aggressorSide": "sell",
            "tradeId": "t1",
        },
    )
    domain = trade_dto_to_domain(trade)
    assert domain.side is OrderSide.SELL

    snap = parse_snapshot_dto(
        "X",
        {
            "marketData": {
                "BI": [{"price": "1", "size": "1"}],
                "OF": [{"Px": "2", "OfferSize": "3"}],
                "LA": {"price": "1.5", "size": "1"},
                "OI": {"size": "99"},
                "timestamp": "2024-01-01T12:00:00Z",
            }
        },
    )
    assert snap.last_price == Decimal("1.5")
    assert len(book_levels_to_domain(snap.bids)) == 1
    assert snap.offers[0] == A3BookLevelDTO(price=Decimal("2"), size=Decimal("3"))


def test_persistence_reexports_and_validators(tmp_path: Path) -> None:
    assert RawStore is not None and ProcessedStore is not None
    store = RawStore(tmp_path / "raw")
    path = store.append(
        kind="instruments",
        environment="simulation",
        symbol="X",
        endpoint_or_message_type="test",
        payload={"ok": True},
        event_timestamp=datetime.now(tz=UTC),
        request_id="r",
        ingestion_run_id="run",
    )
    assert path.exists()
    assert validate_trades([]).issues == ()
    assert validate_bars([]).issues == ()
    assert vb([]).issues == ()


def test_catalog_list_and_replay(tmp_path: Path) -> None:
    catalog = DataCatalog(tmp_path / "c.sqlite")
    now = datetime.now(tz=UTC)
    checksum = "a" * 64
    manifest = DatasetManifest(
        dataset_id="ds-1",
        version="1",
        source="a3",
        instruments=("a3:X",),
        time_range=TimeRange(start=now - timedelta(hours=1), end=now),
        granularity="1m",
        schema_version="1.0",
        checksum=checksum,
        row_count=1,
        storage_path="processed/ds-1.jsonl",
        created_at=now,
    )
    catalog.register_dataset(manifest, kind="bars", provider="a3")
    assert catalog.list_datasets(provider="a3", kind="bars", symbol="a3:X")
    assert catalog.find_latest(provider="a3", symbol="a3:X", timeframe="1m") is not None
    entry = load_catalog_entry(catalog, "ds-1")
    assert entry.dataset_id == "ds-1"
    with pytest.raises(KeyError):
        load_catalog_entry(catalog, "missing")
    assert catalog.verify_dataset("missing") is False


def test_risk_gate_paths(tmp_path: Path) -> None:
    root = Path.cwd()
    cfg = load_a3_config(root / "config" / "exchanges" / "a3.yaml")
    ks = KillSwitch(tmp_path / "kill.json")
    ks.save(KillSwitchState(block_all_orders=False, block_production=True))
    gate = DefaultPreTradeRiskGate(cfg, ks)

    intent = OrderIntent(
        intent_id="r1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="a3:DLR/DIC24",
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("1000"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    ctx = TradingContext(
        environment="simulation",
        account="SIM-001",
        is_production=False,
        execution_enabled=True,
        allow_live_orders=False,
        live_env_confirmed=False,
        last_market_data_at=datetime.now(tz=UTC),
        last_price=Decimal("1000"),
        open_client_order_ids=frozenset(),
    )
    assert gate.evaluate(intent, ctx).approved

    bad = gate.evaluate(
        intent,
        TradingContext(
            environment="simulation",
            account="SIM-001",
            is_production=False,
            execution_enabled=False,
            allow_live_orders=False,
            live_env_confirmed=False,
            last_market_data_at=None,
            last_price=None,
            open_client_order_ids=frozenset({"r1"}),
        ),
    )
    assert not bad.approved
    assert "execution.disabled" in bad.reasons
    assert "duplicate_client_order_id" in bad.reasons

    cancel = OrderIntent(
        intent_id="c1",
        intent_type=IntentType.CANCEL_ORDER,
        instrument_id="a3:X",
        replace_target_id="o1",
    )
    assert gate.evaluate(cancel, ctx).approved


def test_production_risk_allowlist(tmp_path: Path) -> None:
    root = Path.cwd()
    base = load_a3_config(root / "config" / "exchanges" / "a3.yaml")
    cfg = A3Config(
        enabled=True,
        environment=A3EnvironmentName.PRODUCTION,
        market_data=base.market_data,
        execution=base.execution.__class__(
            enabled=True,
            allow_live_orders=True,
            account_allowlist=("ACC-OK",),
            require_live_confirmation=True,
        ),
        storage=base.storage.__class__(
            raw_root=tmp_path / "raw",
            processed_root=tmp_path / "proc",
            catalog_path=tmp_path / "c.sqlite",
            kill_switch_path=tmp_path / "k.json",
        ),
        risk=base.risk.__class__(
            max_order_quantity=Decimal("10"),
            max_notional=Decimal("100"),
            max_market_data_age_seconds=1,
            symbol_allowlist=("ONLY",),
            reject_if_insufficient_info=True,
        ),
    )
    ks = KillSwitch(tmp_path / "k.json")
    gate = DefaultPreTradeRiskGate(cfg, ks)
    intent = OrderIntent(
        intent_id="p1",
        intent_type=IntentType.PLACE_ORDER,
        instrument_id="a3:NOPE",
        side=OrderSide.BUY,
        quantity=Decimal("50"),
        price=Decimal("10"),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
    )
    decision = gate.evaluate(
        intent,
        TradingContext(
            environment="production",
            account="BAD",
            is_production=True,
            execution_enabled=True,
            allow_live_orders=False,
            live_env_confirmed=False,
            last_market_data_at=datetime.now(tz=UTC) - timedelta(hours=1),
            last_price=Decimal("10"),
            open_client_order_ids=frozenset(),
        ),
    )
    assert not decision.approved
    assert "symbol_not_allowlisted" in decision.reasons
    assert "quantity_above_max" in decision.reasons
