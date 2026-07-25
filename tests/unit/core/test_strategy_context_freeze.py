"""StrategyContext congela parameters."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import ClockMode, ClockSpeed
from quantlab.core.types.portfolio import SimulationClock


def test_strategy_context_parameters_frozen() -> None:
    ctx = StrategyContext(
        clock=SimulationClock(
            current_time=datetime(2024, 1, 1, tzinfo=UTC),
            mode=ClockMode.EVENT_DRIVEN,
            speed=ClockSpeed.ACCELERATED,
        ),
        parameters={"alpha": 1},
    )
    with pytest.raises(TypeError):
        ctx.parameters["alpha"] = 2  # type: ignore[index]
