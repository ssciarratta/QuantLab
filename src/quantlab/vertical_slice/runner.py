"""Vertical slice de Fase 2 — demostración end-to-end sin simulación real."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from quantlab.core.contracts.strategy import Strategy, StrategyContext
from quantlab.core.types.enums import ClockMode, ClockSpeed, EventType, ExperimentStatus
from quantlab.core.types.instrument import Instrument
from quantlab.core.types.manifests import (
    DatasetManifest,
    ExecutionModelVersions,
    ExperimentManifest,
    TimeRange,
)
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent
from quantlab.core.types.portfolio import SimulationClock
from quantlab.core.types.serialization import dataclass_to_dict
from quantlab.infra.config import AppConfig, resolve_config, validate_config
from quantlab.infra.logging import configure_logging, get_logger
from quantlab.infra.utils import (
    get_git_commit,
    get_platform_info,
    get_python_version,
    hash_dependencies,
)
from quantlab.research.strategies.dummy_strategy import DummyStrategy

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class VerticalSliceResult:
    """Resultado del flujo mínimo de Fase 2."""

    instrument: Instrument
    dataset_manifest: DatasetManifest
    experiment_manifest: ExperimentManifest
    intents: tuple[OrderIntent, ...]
    config: AppConfig


def find_project_root(start: Path | None = None) -> Path:
    """Localiza la raíz del proyecto (contiene config/ y pyproject.toml)."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "config").is_dir():
            return candidate
    msg = "No se encontró la raíz del proyecto QuantLab"
    raise FileNotFoundError(msg)


def build_sample_instrument() -> Instrument:
    """Instrumento sintético para el vertical slice."""
    return Instrument(
        instrument_id="BTC-USDT-binance",
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        venue_id="binance",
        tick_size=Decimal("0.01"),
        lot_size=Decimal("0.00001"),
        min_notional=Decimal("10"),
    )


def build_sample_dataset_manifest(instrument: Instrument, config: AppConfig) -> DatasetManifest:
    """DatasetManifest sintético referenciando storage local."""
    now = datetime.now(tz=UTC)
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2024, 1, 2, tzinfo=UTC)
    storage = Path(config.quantlab.data_root) / "processed" / "demo" / instrument.symbol
    return DatasetManifest(
        dataset_id="demo-btcusdt-1m",
        version="v1",
        source="synthetic-vertical-slice",
        instruments=(instrument.instrument_id,),
        time_range=TimeRange(start=start, end=end),
        granularity="1m",
        schema_version="1.0",
        checksum="0" * 64,
        row_count=1440,
        storage_path=str(storage),
        created_at=now,
    )


def build_experiment_manifest(
    dataset: DatasetManifest,
    config: AppConfig,
    *,
    experiment_id: str | None = None,
) -> ExperimentManifest:
    """ExperimentManifest con metadatos de reproducibilidad del entorno."""
    now = datetime.now(tz=UTC)
    resolved = config.model_dump()
    checksum = hashlib.sha256(
        json.dumps(resolved, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return ExperimentManifest(
        experiment_id=experiment_id or str(uuid4()),
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.version,
        resolved_config=resolved,
        seed=config.experiment.default_seed,
        git_commit=get_git_commit(),
        python_version=get_python_version(),
        dependency_versions_or_hash=hash_dependencies(),
        platform=get_platform_info(),
        strategy_version=config.experiment.strategy_version,
        execution_model_versions=ExecutionModelVersions(
            fee_model="none-phase2",
            slippage_model="none-phase2",
            latency_model="none-phase2",
            fill_model="none-phase2",
        ),
        artifacts_produced=("vertical_slice_log",),
        created_at=now,
        checksum=checksum,
        status=ExperimentStatus.DRAFT,
    )


def build_bar_event(instrument: Instrument, bar: Bar | None = None) -> MarketEvent:
    """MarketEvent de tipo BAR para probar Strategy."""
    sample_bar = bar or Bar(
        instrument_id=instrument.instrument_id,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.5"),
        volume=Decimal("12.5"),
        timestamp_open=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
        timestamp_close=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
        timeframe="1m",
    )
    payload: dict[str, Any] = {"bar": dataclass_to_dict(sample_bar)}
    return MarketEvent(
        event_id=str(uuid4()),
        event_type=EventType.BAR,
        timestamp=sample_bar.timestamp_close,
        instrument_id=instrument.instrument_id,
        payload=payload,
    )


def build_strategy_context(bar_event: MarketEvent) -> StrategyContext:
    """Contexto mínimo de simulación."""
    clock = SimulationClock(
        current_time=bar_event.timestamp,
        mode=ClockMode.EVENT_DRIVEN,
        speed=ClockSpeed.ACCELERATED,
    )
    return StrategyContext(clock=clock, portfolio_state=None, parameters={})


def run_vertical_slice(
    project_root: Path | None = None,
    *,
    environment: str | None = None,
    strategy: Strategy | None = None,
) -> VerticalSliceResult:
    """
    Ejecuta el flujo mínimo de Fase 2:
    config → logging → instrument → manifests → strategy → intents.
    """
    root = find_project_root(project_root)
    config = resolve_config(root / "config", environment=environment)
    validate_config(config)
    configure_logging(config.logging)

    log = get_logger("vertical_slice")
    log.info(
        "vertical_slice_start",
        environment=config.quantlab.environment,
        project=config.quantlab.project_name,
    )

    instrument = build_sample_instrument()
    dataset_manifest = build_sample_dataset_manifest(instrument, config)
    experiment_manifest = build_experiment_manifest(dataset_manifest, config)

    active_strategy = strategy or DummyStrategy(
        parameters={"quantity": "0.01", "price": "100.0"},
    )
    bar_event = build_bar_event(instrument)
    context = build_strategy_context(bar_event)
    intents = active_strategy.on_event(bar_event, context)

    log.info(
        "vertical_slice_complete",
        experiment_id=experiment_manifest.experiment_id,
        dataset_id=dataset_manifest.dataset_id,
        intents_count=len(intents),
        intent_types=[i.intent_type.value for i in intents],
    )

    return VerticalSliceResult(
        instrument=instrument,
        dataset_manifest=dataset_manifest,
        experiment_manifest=experiment_manifest,
        intents=intents,
        config=config,
    )


def main() -> None:
    """Entry point CLI."""
    run_vertical_slice()


if __name__ == "__main__":
    main()
