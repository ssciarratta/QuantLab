"""Protocolos de políticas de ejecución (Fase 5)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from quantlab.core.types.enums import LiquidityType, OrderSide
from quantlab.core.types.market import Bar
from quantlab.execution.fees import FeeAssessment
from quantlab.execution.latency import LatencyDecision


class SlippageModel(Protocol):
    """Ajusta el precio de fill de forma adversa al trader."""

    @property
    def model_id(self) -> str: ...

    def apply(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        bar: Bar,
    ) -> Decimal:
        """Retorna precio de fill ajustado (Decimal)."""
        ...


class LatencyModel(Protocol):
    """Determina cuándo una intención se vuelve ejecutable."""

    @property
    def model_id(self) -> str: ...

    def resolve(
        self,
        *,
        submit_index: int,
        submit_time: datetime,
        series_length: int,
    ) -> LatencyDecision:
        """Índice de barra efectiva o rechazo si cae fuera de la serie."""
        ...


class FeeModel(Protocol):
    """Calcula comisión de un fill."""

    @property
    def model_id(self) -> str: ...

    def assess(
        self,
        *,
        side: OrderSide,
        price: Decimal,
        quantity: Decimal,
        liquidity: LiquidityType,
    ) -> FeeAssessment: ...
