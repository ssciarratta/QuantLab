"""Explicabilidad de AlphaScanner (Fase 13)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quantlab.research.alpha import AssetScore, ScannerResult


@dataclass(frozen=True, slots=True)
class ScoreExplanation:
    instrument_id: str
    composite: float
    drivers: tuple[str, ...]


def explain_scores(result: ScannerResult, *, top: int = 3) -> tuple[ScoreExplanation, ...]:
    out: list[ScoreExplanation] = []
    for score in result.scores[:top]:
        out.append(
            ScoreExplanation(
                instrument_id=score.instrument_id,
                composite=score.composite,
                drivers=_drivers(score),
            )
        )
    return tuple(out)


def _drivers(score: AssetScore) -> tuple[str, ...]:
    parts = [
        ("volatility", score.volatility),
        ("volume", score.volume_score),
        ("liquidity", score.liquidity_score),
    ]
    parts.sort(key=lambda x: -x[1])
    return tuple(f"{name}={value:.6g}" for name, value in parts)
