"""Schedules de comisiones VIP0 por venue y tipo de mercado (research)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.research.sim.symbol_map import MARKET_TYPES, VENUES


@dataclass(frozen=True, slots=True)
class VenueFeeSchedule:
    venue: str
    market_type: str
    maker_bps: Decimal
    taker_bps: Decimal
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "market_type": self.market_type,
            "maker_bps": str(self.maker_bps),
            "taker_bps": str(self.taker_bps),
            "maker_pct": str(self.maker_bps / Decimal("100")),
            "taker_pct": str(self.taker_bps / Decimal("100")),
            "notes": self.notes,
        }


def _sched(
    venue: str,
    market_type: str,
    maker: str,
    taker: str,
    notes: str,
) -> VenueFeeSchedule:
    return VenueFeeSchedule(
        venue=venue,
        market_type=market_type,
        maker_bps=Decimal(maker),
        taker_bps=Decimal(taker),
        notes=notes,
    )


PRESETS: dict[tuple[str, str], VenueFeeSchedule] = {
    ("binance", "spot"): _sched(
        "binance",
        "spot",
        "10",
        "10",
        "Binance Spot VIP0: maker/taker 0.10%",
    ),
    ("binance", "futures"): _sched(
        "binance",
        "futures",
        "2",
        "5",
        "Binance USDT-M Futures VIP0: maker 0.02% / taker 0.05%",
    ),
    ("okx", "spot"): _sched(
        "okx",
        "spot",
        "8",
        "10",
        "OKX Spot VIP0 aprox: maker 0.08% / taker 0.10%",
    ),
    ("okx", "futures"): _sched(
        "okx",
        "futures",
        "2",
        "5",
        "OKX USDT perpetual VIP0: maker 0.02% / taker 0.05%",
    ),
    ("bybit", "spot"): _sched(
        "bybit",
        "spot",
        "10",
        "10",
        "Bybit Spot VIP0: maker/taker 0.10%",
    ),
    ("bybit", "futures"): _sched(
        "bybit",
        "futures",
        "2",
        "5.5",
        "Bybit USDT perpetual VIP0: maker 0.02% / taker 0.055%",
    ),
    ("hyperliquid", "spot"): _sched(
        "hyperliquid",
        "spot",
        "4",
        "7",
        "Hyperliquid Spot VIP0 aprox: maker 0.04% / taker 0.07%",
    ),
    ("hyperliquid", "futures"): _sched(
        "hyperliquid",
        "futures",
        "1.5",
        "4.5",
        "Hyperliquid perp VIP0: maker 0.015% / taker 0.045%",
    ),
}


def get_fee_schedule(venue: str, market_type: str) -> VenueFeeSchedule:
    """Devuelve schedule VIP0 para venue/market_type."""
    v = venue.strip().lower()
    mt = market_type.strip().lower()
    if v not in VENUES:
        raise ValidationError(f"venue desconocido: {venue!r}")
    if mt not in MARKET_TYPES:
        raise ValidationError(f"market_type inválido: {market_type!r}")
    key = (v, mt)
    sched = PRESETS.get(key)
    if sched is None:
        raise ValidationError(f"fee schedule no definido: {v}/{mt}")
    return sched


def list_fee_schedules() -> list[dict[str, Any]]:
    """Lista todos los presets como dicts serializables."""
    return [s.to_dict() for s in PRESETS.values()]
