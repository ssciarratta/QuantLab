"""Recomendación de estrategia Sim para señales pairwise (P4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantlab.research.alpha.models import AlphaSignal

__all__ = [
    "PairwiseStrategyRecommendation",
    "recommend_strategy_for_signal",
    "signal_dict_with_recommendation",
]


@dataclass(frozen=True, slots=True)
class PairwiseStrategyRecommendation:
    strategy_id: str
    label: str
    rationale: str

    def to_dict(self) -> dict[str, str]:
        return {
            "strategy_id": self.strategy_id,
            "label": self.label,
            "rationale": self.rationale,
        }


_SIGNAL_STRATEGY: dict[str, PairwiseStrategyRecommendation] = {
    "lagged_correlation": PairwiseStrategyRecommendation(
        strategy_id="pairs_trading",
        label="Pairs Trading",
        rationale="Lead-lag en retornos → proxy pairs_lag en Sim.",
    ),
    "cointegration": PairwiseStrategyRecommendation(
        strategy_id="cointegration",
        label="Cointegration",
        rationale="Equilibrio largo plazo → mean-reversion proxy.",
    ),
    "pair_spread": PairwiseStrategyRecommendation(
        strategy_id="pairs_trading",
        label="Pairs Trading",
        rationale="Spread z-score → entrada/salida por desviación.",
    ),
    "contemporary_correlation": PairwiseStrategyRecommendation(
        strategy_id="momentum",
        label="Momentum",
        rationale="Alta correlación → proxy trend en pierna líder.",
    ),
}

_DEFAULT = PairwiseStrategyRecommendation(
    strategy_id="pairs_trading",
    label="Pairs Trading",
    rationale="Señal pairwise genérica → proxy pairs.",
)


def recommend_strategy_for_signal(
    signal_type: str,
    *,
    lag: int | None = None,
) -> PairwiseStrategyRecommendation:
    key = signal_type.strip().lower()
    rec = _SIGNAL_STRATEGY.get(key, _DEFAULT)
    if key == "lagged_correlation" and lag is not None and lag > 0:
        return PairwiseStrategyRecommendation(
            strategy_id=rec.strategy_id,
            label=rec.label,
            rationale=f"{rec.rationale} Lag={lag}.",
        )
    return rec


def signal_dict_with_recommendation(sig: AlphaSignal) -> dict[str, Any]:
    """Serializa señal + ``recommended_strategy`` para API/UI."""
    d = sig.to_dict()
    rec = recommend_strategy_for_signal(sig.signal_type, lag=sig.lag)
    d["recommended_strategy"] = rec.to_dict()
    meta = dict(d.get("metadata") or {})
    meta["recommended_strategy_id"] = rec.strategy_id
    d["metadata"] = meta
    return d
