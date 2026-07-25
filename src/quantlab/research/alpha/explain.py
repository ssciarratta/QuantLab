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


def explain_scores(
    result: ScannerResult,
    *,
    top: int = 3,
    weights: ScannerWeights | None = None,
) -> tuple[ScoreExplanation, ...]:
    out: list[ScoreExplanation] = []
    for score in result.scores[:top]:
        out.append(
            ScoreExplanation(
                instrument_id=score.instrument_id,
                composite=score.composite,
                drivers=_drivers(score, weights=weights),
            )
        )
    return tuple(out)


def _drivers(
    score: AssetScore,
    *,
    weights: ScannerWeights | None = None,
) -> tuple[str, ...]:
    from quantlab.research.alpha import ScannerWeights

    w = weights or ScannerWeights()
    # Contribución aproximada: peso * score crudo (ranking relativo de drivers)
    parts = [
        ("volatility", w.volatility * score.volatility, w.volatility, score.volatility),
        ("volume", w.volume * score.volume_score, w.volume, score.volume_score),
        ("liquidity", w.liquidity * score.liquidity_score, w.liquidity, score.liquidity_score),
    ]
    parts.sort(key=lambda x: -x[1])
    return tuple(
        f"{name}={raw:.6g} (w={weight:.3g}, contrib≈{contrib:.6g})"
        for name, contrib, weight, raw in parts
    )
