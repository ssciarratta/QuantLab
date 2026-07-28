"""Multi-venue capabilities para Alpha Scanner (FASE 6).

No implementa SDKs de Hyperliquid/Bybit/OKX: declara capacidades y permite
ranking combinado cuando hay barras de varios venues. Binance es el unico
con fetch publico cableado en lab hoy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from quantlab.core.types.market import Bar
from quantlab.research.alpha.profiles import score_with_profile
from quantlab.research.alpha.scoring import ScoredRow
from quantlab.research.alpha.universe import (
    BuiltUniverse,
    build_universe_from_symbol_bars,
)

VENUE_BINANCE = "binance"
VENUE_HYPERLIQUID = "hyperliquid"
VENUE_BYBIT = "bybit"
VENUE_OKX = "okx"
VENUE_LAB = "lab"


@dataclass(frozen=True, slots=True)
class VenueCapabilities:
    venue: str
    public_klines: bool
    public_ticker: bool
    order_book: bool
    funding: bool
    open_interest: bool
    spot: bool
    perpetuals: bool
    fetch_implemented: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "public_klines": self.public_klines,
            "public_ticker": self.public_ticker,
            "order_book": self.order_book,
            "funding": self.funding,
            "open_interest": self.open_interest,
            "spot": self.spot,
            "perpetuals": self.perpetuals,
            "fetch_implemented": self.fetch_implemented,
            "notes": self.notes,
        }


_CAPABILITIES: dict[str, VenueCapabilities] = {
    VENUE_BINANCE: VenueCapabilities(
        venue=VENUE_BINANCE,
        public_klines=True,
        public_ticker=True,
        order_book=True,
        funding=True,
        open_interest=True,
        spot=True,
        perpetuals=True,
        fetch_implemented=True,
        notes="Klines publicas cableadas en lab (spot USDT).",
    ),
    VENUE_HYPERLIQUID: VenueCapabilities(
        venue=VENUE_HYPERLIQUID,
        public_klines=True,
        public_ticker=True,
        order_book=True,
        funding=True,
        open_interest=True,
        spot=False,
        perpetuals=True,
        fetch_implemented=True,
        notes="Klines/funding públicos vía POST info (Hyperliquid).",
    ),
    VENUE_BYBIT: VenueCapabilities(
        venue=VENUE_BYBIT,
        public_klines=True,
        public_ticker=True,
        order_book=True,
        funding=True,
        open_interest=True,
        spot=True,
        perpetuals=True,
        fetch_implemented=True,
        notes="Klines linear + funding públicos (Bybit v5).",
    ),
    VENUE_OKX: VenueCapabilities(
        venue=VENUE_OKX,
        public_klines=True,
        public_ticker=True,
        order_book=True,
        funding=True,
        open_interest=True,
        spot=True,
        perpetuals=True,
        fetch_implemented=True,
        notes="Candles + funding públicos (OKX v5).",
    ),
    VENUE_LAB: VenueCapabilities(
        venue=VENUE_LAB,
        public_klines=False,
        public_ticker=False,
        order_book=False,
        funding=False,
        open_interest=False,
        spot=True,
        perpetuals=False,
        fetch_implemented=True,
        notes="Universo sintetico WB:* del lab local.",
    ),
}


def get_venue_capabilities(venue: str) -> VenueCapabilities:
    key = venue.strip().lower()
    if key not in _CAPABILITIES:
        raise ValueError(f"venue desconocido: {venue!r}")
    return _CAPABILITIES[key]


def list_venue_capabilities() -> tuple[VenueCapabilities, ...]:
    return tuple(_CAPABILITIES[k] for k in sorted(_CAPABILITIES))


def assert_venue_fetchable(venue: str) -> VenueCapabilities:
    """Falla si el venue no tiene fetch implementado (evita silencio)."""
    caps = get_venue_capabilities(venue)
    if not caps.fetch_implemented:
        raise NotImplementedError(
            f"venue={venue!r} sin fetch MD implementado "
            f"(capabilities={caps.to_dict()})"
        )
    return caps


@dataclass(frozen=True, slots=True)
class VenueUniverseSlice:
    venue: str
    universe: BuiltUniverse
    capabilities: VenueCapabilities

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "capabilities": self.capabilities.to_dict(),
            "fetched": len(self.universe.initial_symbols),
            "eligible": len(self.universe.eligible_bars),
            "excluded": len(self.universe.exclusions),
        }


@dataclass(frozen=True, slots=True)
class CombinedScanResult:
    profile: str
    rows: tuple[ScoredRow, ...]
    slices: tuple[VenueUniverseSlice, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "rows": [r.to_dict() for r in self.rows],
            "slices": [s.to_dict() for s in self.slices],
            "warnings": list(self.warnings),
            "n_candidates": len([r for r in self.rows if not r.excluded]),
        }


def build_venue_slice(
    *,
    venue: str,
    symbols: Sequence[str],
    bars_by_symbol: Mapping[str, Sequence[Bar]],
    instrument_prefix: str,
    fetch_failures: Mapping[str, str] | None = None,
    network: str = "mainnet",
    market_type: str = "spot",
) -> VenueUniverseSlice:
    caps = get_venue_capabilities(venue)
    built = build_universe_from_symbol_bars(
        venue=venue,
        symbols=symbols,
        bars_by_symbol=bars_by_symbol,
        network=network,
        market_type=market_type,
        instrument_prefix=instrument_prefix,
        fetch_failures=fetch_failures,
    )
    return VenueUniverseSlice(venue=venue, universe=built, capabilities=caps)


def combine_eligible_bars(
    slices: Sequence[VenueUniverseSlice],
) -> dict[str, list[Bar]]:
    """Une barras elegibles; claves ya deben ser instrument_id unicos por venue."""
    out: dict[str, list[Bar]] = {}
    for sl in slices:
        for iid, bars in sl.universe.eligible_bars.items():
            if iid in out:
                raise ValueError(f"instrument_id duplicado entre venues: {iid}")
            out[iid] = bars
    return out


def scan_multi_venue(
    slices: Sequence[VenueUniverseSlice],
    *,
    profile: str = "legacy_v1",
    require_fetch_implemented: bool = True,
) -> CombinedScanResult:
    """Ranking combinado cross-venue sobre barras ya construidas."""
    warnings: list[str] = []
    usable: list[VenueUniverseSlice] = []
    for sl in slices:
        if require_fetch_implemented and not sl.capabilities.fetch_implemented:
            warnings.append(
                f"venue={sl.venue} omitido: fetch_implemented=false"
            )
            continue
        if not sl.capabilities.public_klines:
            warnings.append(f"venue={sl.venue} sin public_klines")
        usable.append(sl)

    if not usable:
        raise ValueError("ningun venue usable para scan multi-venue")

    bars = combine_eligible_bars(usable)
    if not bars:
        raise ValueError("sin barras elegibles en venues usables")

    rows = score_with_profile(bars, profile)
    return CombinedScanResult(
        profile=profile,
        rows=rows,
        slices=tuple(usable),
        warnings=tuple(warnings),
    )


__all__ = [
    "VENUE_BINANCE",
    "VENUE_BYBIT",
    "VENUE_HYPERLIQUID",
    "VENUE_LAB",
    "VENUE_OKX",
    "CombinedScanResult",
    "VenueCapabilities",
    "VenueUniverseSlice",
    "assert_venue_fetchable",
    "build_venue_slice",
    "combine_eligible_bars",
    "get_venue_capabilities",
    "list_venue_capabilities",
    "scan_multi_venue",
]
