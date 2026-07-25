"""Contrato Strategy event-driven (DEC-014)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent
from quantlab.core.types.portfolio import PortfolioState, SimulationClock
from quantlab.core.types.validation import freeze_mapping


@dataclass(frozen=True, slots=True)
class StrategyContext:
    """Contexto inmutable disponible para la estrategia en cada evento."""

    clock: SimulationClock
    portfolio_state: PortfolioState | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameters", freeze_mapping(self.parameters))


@runtime_checkable
class Strategy(Protocol):
    """Contrato event-driven: recibe eventos, produce intenciones."""

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        """Procesa un evento de mercado o lifecycle y retorna intenciones."""
        ...

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        """Adaptador opcional para estrategias bar-based."""
        ...

    def get_parameters(self) -> dict[str, Any]:
        """Parámetros actuales de la estrategia."""
        ...

    def set_parameters(self, params: dict[str, Any]) -> None:
        """Inyecta parámetros (optimización futura).

        La inyección debe realizarse únicamente durante la inicialización u
        optimización previa a la ejecución del backtest — no a mitad de una
        corrida — para preservar la deterministicidad.
        """
        ...

    def get_state(self) -> dict[str, Any]:
        """Estado interno serializable."""
        ...

    def reset(self) -> None:
        """Reinicia la estrategia para una nueva corrida."""
        ...
