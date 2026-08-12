"""Alineación temporal de dos series de barras."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from quantlab.core.types.market import Bar


@dataclass(frozen=True, slots=True)
class AlignedPairBars:
    timestamps: tuple[str, ...]
    closes_a: tuple[float, ...]
    closes_b: tuple[float, ...]
    leg_a: str
    leg_b: str


def align_pair_bars(bars_a: Sequence[Bar], bars_b: Sequence[Bar]) -> AlignedPairBars | None:
    """Inner join por ``timestamp_close`` ISO; retorna None si < 3 puntos."""
    if not bars_a or not bars_b:
        return None
    map_a = {b.timestamp_close.isoformat(): float(b.close) for b in bars_a}
    map_b = {b.timestamp_close.isoformat(): float(b.close) for b in bars_b}
    common = sorted(set(map_a) & set(map_b))
    if len(common) < 3:
        return None
    return AlignedPairBars(
        timestamps=tuple(common),
        closes_a=tuple(map_a[t] for t in common),
        closes_b=tuple(map_b[t] for t in common),
        leg_a=bars_a[0].instrument_id,
        leg_b=bars_b[0].instrument_id,
    )
