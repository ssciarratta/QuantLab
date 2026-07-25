"""Tests de tipos de dominio."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from quantlab.core.exceptions import ManifestError, ValidationError
from quantlab.core.types import (
    DatasetManifest,
    ExecutionModelVersions,
    ExperimentManifest,
    Instrument,
    TimeRange,
)


def test_instrument_is_frozen() -> None:
    instrument = Instrument(
        instrument_id="id",
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        venue_id="binance",
        tick_size=Decimal("0.01"),
        lot_size=Decimal("0.0001"),
        min_notional=Decimal("10"),
    )
    with pytest.raises(AttributeError):
        instrument.symbol = "ETHUSDT"  # type: ignore[misc]


def test_time_range_rejects_invalid_order() -> None:
    start = datetime(2024, 1, 2, tzinfo=UTC)
    end = datetime(2024, 1, 1, tzinfo=UTC)
    with pytest.raises(ValidationError):
        TimeRange(start=start, end=end)


def test_dataset_manifest_serializes() -> None:
    now = datetime.now(tz=UTC)
    manifest = DatasetManifest(
        dataset_id="ds1",
        version="v1",
        source="test",
        instruments=("inst1",),
        time_range=TimeRange(
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        ),
        granularity="1m",
        schema_version="1.0",
        checksum="ab" * 32,
        row_count=100,
        storage_path="/tmp/data",
        created_at=now,
    )
    data = manifest.to_dict()
    assert data["dataset_id"] == "ds1"
    assert data["row_count"] == 100


def test_experiment_manifest_requires_id() -> None:
    now = datetime.now(tz=UTC)
    with pytest.raises(ManifestError):
        ExperimentManifest(
            experiment_id="",
            dataset_id="ds1",
            dataset_version="v1",
            resolved_config={},
            seed=42,
            git_commit="abc",
            python_version="3.11.0",
            dependency_versions_or_hash="deadbeef",
            platform="test",
            strategy_version="0.0.0",
            execution_model_versions=ExecutionModelVersions(
                fee_model="n",
                slippage_model="n",
                latency_model="n",
                fill_model="n",
            ),
            artifacts_produced=(),
            created_at=now,
            checksum="0" * 64,
        )
