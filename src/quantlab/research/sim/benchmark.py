"""Benchmark de tasa anual simple sobre un periodo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Any

_SECONDS_PER_YEAR = Decimal("365") * Decimal("24") * Decimal("3600")


@dataclass(frozen=True, slots=True)
class BenchmarkPeriod:
    """Retorno simple proporcional al tiempo transcurrido."""

    capital: Decimal
    annual_rate: Decimal
    duration: timedelta
    period_return: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "capital": str(self.capital),
            "annual_rate": str(self.annual_rate),
            "duration_seconds": str(int(self.duration.total_seconds())),
            "period_return": str(self.period_return),
        }


def annual_rate_to_period_return(
    capital: Decimal,
    annual_rate: Decimal,
    duration: timedelta,
) -> Decimal:
    """Retorno simple: capital × annual_rate × (segundos / segundos_año)."""
    seconds = Decimal(str(duration.total_seconds()))
    if seconds <= 0:
        return Decimal("0")
    fraction = seconds / _SECONDS_PER_YEAR
    return capital * annual_rate * fraction


def compute_benchmark(
    capital: Decimal,
    annual_rate: Decimal,
    duration: timedelta,
) -> BenchmarkPeriod:
    """Calcula retorno de benchmark y lo empaqueta con ``to_dict``."""
    period_return = annual_rate_to_period_return(capital, annual_rate, duration)
    return BenchmarkPeriod(
        capital=capital,
        annual_rate=annual_rate,
        duration=duration,
        period_return=period_return,
    )
