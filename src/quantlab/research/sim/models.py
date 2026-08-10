"""Modelos de resultado — simulador multi-venue."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class SimOverlayResult:
    """Equity final tras overlay leverage/funding/liquidación."""

    initial_equity: Decimal
    final_equity: Decimal
    pnl: Decimal
    pnl_pct: Decimal
    leverage: Decimal
    liquidated: bool
    liquidation_bar_index: int | None
    total_funding: Decimal
    funding_applied: bool
    liquidation_simulated: bool
    equity_curve: tuple[tuple[str, str], ...] = ()  # (iso_ts, equity_str)

    def to_dict(self) -> dict[str, Any]:
        return {
            "initial_equity": str(self.initial_equity),
            "final_equity": str(self.final_equity),
            "pnl": str(self.pnl),
            "pnl_pct": str(self.pnl_pct),
            "leverage": str(self.leverage),
            "liquidated": self.liquidated,
            "liquidation_bar_index": self.liquidation_bar_index,
            "total_funding": str(self.total_funding),
            "funding_applied": self.funding_applied,
            "liquidation_simulated": self.liquidation_simulated,
            "equity_curve": [{"ts": t, "equity": e} for t, e in self.equity_curve],
        }


@dataclass(frozen=True, slots=True)
class SimCompareRow:
    """Una fila de la tabla comparativa."""

    venue: str
    market_type: str  # spot | futures
    underlying: str
    instrument_id: str
    leverage: Decimal
    strategy_id: str
    ok: bool
    overlay: SimOverlayResult | None = None
    backtest: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "market_type": self.market_type,
            "underlying": self.underlying,
            "instrument_id": self.instrument_id,
            "leverage": str(self.leverage),
            "strategy_id": self.strategy_id,
            "ok": self.ok,
            "overlay": self.overlay.to_dict() if self.overlay else None,
            "backtest": self.backtest,
            "error": self.error,
        }
