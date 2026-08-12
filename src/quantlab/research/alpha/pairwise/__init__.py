"""Pairwise package."""

from quantlab.research.alpha.pairwise.align import AlignedPairBars, align_pair_bars
from quantlab.research.alpha.pairwise.costs import estimate_pair_cost_bps
from quantlab.research.alpha.pairwise.mc_stress import stress_hedge_ratio
from quantlab.research.alpha.pairwise.recommend import (
    PairwiseStrategyRecommendation,
    recommend_strategy_for_signal,
    signal_dict_with_recommendation,
)
from quantlab.research.alpha.pairwise.universe import PairCandidate, generate_pair_candidates

__all__ = [
    "AlignedPairBars",
    "PairCandidate",
    "PairwiseStrategyRecommendation",
    "align_pair_bars",
    "estimate_pair_cost_bps",
    "generate_pair_candidates",
    "recommend_strategy_for_signal",
    "signal_dict_with_recommendation",
    "stress_hedge_ratio",
]
