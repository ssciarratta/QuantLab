"""Explicabilidad de AlphaScanner (Fase 13 / TD-06)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quantlab.research.alpha import AssetScore, ScannerResult, ScannerWeights


@dataclass(frozen=True, slots=True)
class ScoreExplanation:
    instrument_id: str
    composite: float
    drivers: tuple[str, ...]
    contrib_sum: float


def explain_scores(
    result: ScannerResult,
    *,
    top: int = 3,
    weights: ScannerWeights | None = None,
) -> tuple[ScoreExplanation, ...]:
    out: list[ScoreExplanation] = []
    for score in result.scores[:top]:
        drivers, contrib_sum = _drivers(score, weights=weights)
        out.append(
            ScoreExplanation(
                instrument_id=score.instrument_id,
                composite=score.composite,
                drivers=drivers,
                contrib_sum=contrib_sum,
            )
        )
    return tuple(out)


def _drivers(
    score: AssetScore,
    *,
    weights: ScannerWeights | None = None,
) -> tuple[tuple[str, ...], float]:
    from quantlab.research.alpha import ScannerWeights

    w = weights or ScannerWeights()
    # Contribución exacta: peso * componente normalizado (misma fórmula del scanner)
    parts = [
        ("volatility", w.volatility * score.volatility_n, w.volatility, score.volatility),
        ("volume", w.volume * score.volume_n, w.volume, score.volume_score),
        ("liquidity", w.liquidity * score.liquidity_n, w.liquidity, score.liquidity_score),
    ]
    contrib_sum = sum(p[1] for p in parts)
    parts.sort(key=lambda x: -x[1])
    drivers = tuple(
        (
            f"{name}={raw:.6g} (n={contrib / weight if weight else 0.0:.6g}, w={weight:.3g}"
            f", contrib={contrib:.6g}"
            f", share={((contrib / contrib_sum) if contrib_sum else 0.0):.3g})"
        )
        for name, contrib, weight, raw in parts
    )
    return drivers, round(contrib_sum, 8)
