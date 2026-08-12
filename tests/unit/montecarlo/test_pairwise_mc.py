"""Tests MC stress pairwise."""

from __future__ import annotations

from quantlab.research.alpha.pairwise.mc_stress import stress_hedge_ratio


def test_stress_hedge_ratio_percentiles() -> None:
    out = stress_hedge_ratio(1.0, n_shocks=200, shock_std=0.02)
    assert out["p50"] <= out["p95"] <= out["max"]
