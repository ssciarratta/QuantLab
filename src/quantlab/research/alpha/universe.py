"""Construcción de universo para Alpha Scanner (FASE 2)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from quantlab.core.types.market import Bar
from quantlab.research.alpha.models import ExclusionRecord
from quantlab.research.alpha.quality import (
    EligibilityConfig,
    EligibilityResult,
    evaluate_eligibility,
)


@dataclass(frozen=True, slots=True)
class UniverseInstrument:
    venue: str
    network: str
    original_symbol: str
    normalized_instrument: str
    market_type: str
    status: str = "active"

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "network": self.network,
            "original_symbol": self.original_symbol,
            "normalized_instrument": self.normalized_instrument,
            "market_type": self.market_type,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class BuiltUniverse:
    instruments: tuple[UniverseInstrument, ...]
    bars_by_instrument: dict[str, list[Bar]]
    eligibility: tuple[EligibilityResult, ...]
    exclusions: tuple[ExclusionRecord, ...]
    initial_symbols: tuple[str, ...]

    @property
    def eligible_bars(self) -> dict[str, list[Bar]]:
        ok = {e.instrument_id for e in self.eligibility if e.eligible}
        return {k: v for k, v in self.bars_by_instrument.items() if k in ok}


def build_universe_from_symbol_bars(
    *,
    venue: str,
    symbols: Sequence[str],
    bars_by_symbol: Mapping[str, Sequence[Bar]],
    network: str = "mainnet",
    market_type: str = "spot",
    instrument_prefix: str = "BN:",
    eligibility_config: EligibilityConfig | None = None,
    fetch_failures: Mapping[str, str] | None = None,
) -> BuiltUniverse:
    """Arma universo determinista; registra exclusiones tipadas (sin silencio)."""
    cfg = eligibility_config or EligibilityConfig()
    failures = {k.upper(): v for k, v in dict(fetch_failures or {}).items()}
    ordered = list(dict.fromkeys(s.strip().upper() for s in symbols if s.strip()))

    instruments: list[UniverseInstrument] = []
    eligibility: list[EligibilityResult] = []
    exclusions: list[ExclusionRecord] = []
    bars_out: dict[str, list[Bar]] = {}

    bars_upper = {k.upper(): v for k, v in bars_by_symbol.items()}

    for sym in ordered:
        iid = f"{instrument_prefix}{sym}"
        instruments.append(
            UniverseInstrument(
                venue=venue,
                network=network,
                original_symbol=sym,
                normalized_instrument=iid,
                market_type=market_type,
                status="active",
            )
        )
        bars = bars_upper.get(sym)
        if sym in failures:
            ev = evaluate_eligibility(
                iid,
                None,
                config=cfg,
                fetch_failed=True,
                fetch_error=failures[sym],
            )
        elif bars is None:
            ev = evaluate_eligibility(
                iid,
                None,
                config=cfg,
                fetch_failed=True,
                fetch_error="klines omitidas o inválidas",
            )
        else:
            bars_list = list(bars)
            bars_out[iid] = bars_list
            ev = evaluate_eligibility(iid, bars_list, config=cfg)

        eligibility.append(ev)
        if not ev.eligible:
            exclusions.append(
                ExclusionRecord(
                    symbol=sym,
                    reasons=tuple(r.value for r in ev.reasons),
                    detail=ev.detail,
                )
            )

    return BuiltUniverse(
        instruments=tuple(instruments),
        bars_by_instrument=bars_out,
        eligibility=tuple(eligibility),
        exclusions=tuple(exclusions),
        initial_symbols=tuple(ordered),
    )


def exclusion_reason_counts(exclusions: Sequence[ExclusionRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ex in exclusions:
        for r in ex.reasons:
            counts[r] = counts.get(r, 0) + 1
    return counts


__all__ = [
    "BuiltUniverse",
    "UniverseInstrument",
    "build_universe_from_symbol_bars",
    "exclusion_reason_counts",
]
