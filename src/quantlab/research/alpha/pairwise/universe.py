"""Generación de pares candidatos (mismo venue/market)."""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from quantlab.core.types.market import Bar


@dataclass(frozen=True, slots=True)
class PairCandidate:
    leg_a: str
    leg_b: str
    liquidity_score: float

    @property
    def key(self) -> tuple[str, str]:
        a, b = sorted((self.leg_a, self.leg_b))
        return (a, b)


def _liquidity_proxy(bars: Sequence[Bar]) -> float:
    if not bars:
        return 0.0
    tail = bars[-min(24, len(bars)) :]
    return float(sum(float(b.volume) for b in tail) / len(tail))


def generate_pair_candidates(
    bars_by_instrument: Mapping[str, Sequence[Bar]],
    *,
    max_pairs: int = 500,
    min_bars: int = 50,
    min_liquidity: float = 0.0,
) -> tuple[PairCandidate, ...]:
    """Pares unordered same-universe; prioriza liquidez conjunta."""
    eligible = [
        iid
        for iid, bars in bars_by_instrument.items()
        if len(bars) >= min_bars and _liquidity_proxy(bars) >= min_liquidity
    ]
    pairs: list[PairCandidate] = []
    for a, b in itertools.combinations(sorted(eligible), 2):
        liq = min(_liquidity_proxy(bars_by_instrument[a]), _liquidity_proxy(bars_by_instrument[b]))
        pairs.append(PairCandidate(leg_a=a, leg_b=b, liquidity_score=liq))
    pairs.sort(key=lambda p: p.liquidity_score, reverse=True)
    return tuple(pairs[: max(0, max_pairs)])
