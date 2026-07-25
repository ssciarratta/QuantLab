"""Cierre residuales no críticos self-audit: R3/R5/R9, TD-06/09/12, OPS-PROM."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import patch

import pytest

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import IntentType
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent
from quantlab.core.types.results import EquityPoint
from quantlab.core.types.validation import freeze_mapping
from quantlab.features.indicators import ATRIndicator
from quantlab.features.store import FeatureStore
from quantlab.infra.ops_metrics import OpsMetrics, get_ops_metrics, render_prometheus_text
from quantlab.metrics.engine import calmar_ratio, max_drawdown
from quantlab.simulation import BarSimulationEngine, SimulationConfig
from quantlab.simulation.portfolio_tracker import PortfolioTracker


def test_r9_freeze_mapping_deep_nested_immutable() -> None:
    frozen = freeze_mapping({"a": 1, "nested": {"x": [1, {"y": 2}]}, "tags": {"a", "b"}})
    assert isinstance(frozen, MappingProxyType)
    assert isinstance(frozen["nested"], MappingProxyType)
    assert isinstance(frozen["nested"]["x"], tuple)
    assert isinstance(frozen["nested"]["x"][1], MappingProxyType)
    assert isinstance(frozen["tags"], frozenset)

    with pytest.raises(TypeError):
        frozen["a"] = 9  # type: ignore[index]
    with pytest.raises(TypeError):
        frozen["nested"]["x"] = 1  # type: ignore[index]
    with pytest.raises(TypeError):
        frozen["nested"]["x"][1]["y"] = 3  # type: ignore[index]


def test_r3_atr_method_sma_tr_not_wilder() -> None:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars: list[Bar] = []
    for i, c in enumerate(("10", "12", "11", "13", "14", "15")):
        px = Decimal(c)
        t0 = base + timedelta(minutes=i)
        bars.append(
            Bar(
                instrument_id="X",
                open=px,
                high=px + Decimal("1"),
                low=px - Decimal("1"),
                close=px,
                volume=Decimal("1"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    series = ATRIndicator(period=3).transform(bars)
    assert series.points
    assert all(p.metadata.get("method") == "sma_tr" for p in series.points)
    assert "sma_tr" in (ATRIndicator.__doc__ or "")


def test_r5_calmar_bar_based_not_calendar() -> None:
    curve_a = (
        EquityPoint(datetime(2024, 1, 1, tzinfo=UTC), Decimal("100")),
        EquityPoint(datetime(2024, 1, 2, tzinfo=UTC), Decimal("110")),
        EquityPoint(datetime(2024, 1, 3, tzinfo=UTC), Decimal("90")),
    )
    curve_b = (
        EquityPoint(datetime(2024, 1, 1, tzinfo=UTC), Decimal("100")),
        EquityPoint(datetime(2024, 6, 1, tzinfo=UTC), Decimal("110")),
        EquityPoint(datetime(2024, 12, 1, tzinfo=UTC), Decimal("90")),
    )
    assert calmar_ratio(curve_a) == calmar_ratio(curve_b)
    n = len(curve_a) - 1
    total_return = (90 - 100) / 100
    ann = total_return * (252.0 / n)
    mdd = max_drawdown(curve_a)
    assert abs(calmar_ratio(curve_a) - (ann / mdd)) < 1e-12


def test_td12_mark_equity_twice_per_bar() -> None:
    calls: list[datetime] = []
    original = PortfolioTracker.mark_equity

    def wrapped(self: PortfolioTracker, marks: dict[str, Decimal], timestamp: datetime) -> Any:
        calls.append(timestamp)
        return original(self, marks, timestamp)

    base = datetime(2024, 6, 1, tzinfo=UTC)
    bars = [
        Bar(
            instrument_id="X",
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("10"),
            timestamp_open=base,
            timestamp_close=base + timedelta(minutes=1),
            timeframe="1m",
        )
    ]

    class _Hold:
        def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
            return (
                OrderIntent(
                    intent_id="noop",
                    intent_type=IntentType.NO_ACTION,
                    instrument_id=event.instrument_id,
                ),
            )

        def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
            return ()

        def get_parameters(self) -> dict[str, Any]:
            return {}

        def set_parameters(self, params: dict[str, Any]) -> None:
            return None

        def get_state(self) -> dict[str, Any]:
            return {}

        def reset(self) -> None:
            return None

    with patch.object(PortfolioTracker, "mark_equity", wrapped):
        result = BarSimulationEngine(SimulationConfig(experiment_id="td12")).run(_Hold(), bars)

    assert len(calls) == 2
    assert calls[0] == calls[1] == bars[0].timestamp_close
    assert len(result.equity_curve) == 1
    assert len(result.portfolio_snapshots) == 1


def test_ops_prometheus_export() -> None:
    m = OpsMetrics()
    m.inc("live_gate.blocked", 2)
    m.inc("batch.failed_jobs", 1)
    text = m.render_prometheus_text()
    assert "# TYPE live_gate_blocked counter" in text
    assert "live_gate_blocked 2" in text
    assert "batch_failed_jobs 1" in text

    get_ops_metrics().reset()
    get_ops_metrics().inc("health.runs", 3)
    assert "health_runs 3" in render_prometheus_text()
    get_ops_metrics().reset()


def test_td09_feature_store_rejects_remote_url(tmp_path: Path) -> None:
    FeatureStore(tmp_path / "local_ok")
    with pytest.raises(ValidationError, match="filesystem local"):
        FeatureStore(Path("s3://bucket/features"))
    with pytest.raises(ValidationError, match="filesystem local"):
        FeatureStore(Path("https://example.com/store"))
