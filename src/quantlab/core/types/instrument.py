"""Instrument y Venue."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import InstrumentStatus
from quantlab.core.types.validation import (
    freeze_mapping,
    require_non_empty_str,
    require_positive,
)


@dataclass(frozen=True, slots=True)
class Instrument:
    """Activo negociable con reglas de mercado."""

    instrument_id: str
    symbol: str
    base_asset: str
    quote_asset: str
    venue_id: str
    tick_size: Decimal
    lot_size: Decimal
    min_notional: Decimal
    status: InstrumentStatus = InstrumentStatus.ACTIVE
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty_str(self.instrument_id, "instrument_id")
        require_non_empty_str(self.symbol, "symbol")
        require_non_empty_str(self.base_asset, "base_asset")
        require_non_empty_str(self.quote_asset, "quote_asset")
        require_non_empty_str(self.venue_id, "venue_id")
        if self.base_asset.strip() == self.quote_asset.strip():
            raise ValidationError("base_asset y quote_asset deben ser distintos")
        require_positive(self.tick_size, "tick_size")
        require_positive(self.lot_size, "lot_size")
        require_positive(self.min_notional, "min_notional")
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class VenueConstraints:
    """Restricciones operativas de un venue."""

    rate_limit_per_second: int | None = None
    min_order_size: Decimal | None = None


@dataclass(frozen=True, slots=True)
class Venue:
    """Exchange o lugar de ejecución."""

    venue_id: str
    name: str
    timezone: str
    fee_schedule_ref: str
    latency_profile_ref: str
    constraints: VenueConstraints = field(default_factory=VenueConstraints)

    def __post_init__(self) -> None:
        require_non_empty_str(self.venue_id, "venue_id")
        require_non_empty_str(self.name, "name")
        require_non_empty_str(self.timezone, "timezone")
