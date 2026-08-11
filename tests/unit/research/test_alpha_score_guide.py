"""Tests: guía legible del score Alpha Scanner."""

from __future__ import annotations

from quantlab.research.alpha.recommend import recommend_for_score
from quantlab.research.alpha.score_guide import explain_composite_score, score_band


def test_score_band_ranges() -> None:
    assert score_band(0.2)["id"] == "weak"
    assert score_band(0.4)["id"] == "low"
    assert score_band(0.55)["id"] == "good"
    assert score_band(0.55)["optimal_for_testing"] is True
    assert score_band(0.8)["id"] == "strong"
    assert score_band(0.95)["id"] == "top"


def test_explain_composite_score_plain_spanish() -> None:
    ex = explain_composite_score(
        {
            "composite": 0.82,
            "underlying": "BTC",
            "components": [
                {
                    "name": "momentum",
                    "normalized": 0.9,
                    "weight": 0.4,
                    "contribution": 0.36,
                    "available": True,
                },
                {
                    "name": "trend_quality",
                    "normalized": 0.8,
                    "weight": 0.25,
                    "contribution": 0.2,
                    "available": True,
                },
            ],
        },
        profile="trend",
        family="trend",
    )
    assert ex["band"]["id"] == "strong"
    assert "0.50" in ex["ranges_help"]
    assert "Tendenciales" in ex["headline"] or "tendencial" in ex["headline"].lower()
    assert ex["factors"]
    assert len(ex["next_steps"]) >= 3
    assert "rentabilidad" in ex["what_is"].lower() or "rentabilidad" in ex["note"].lower()


def test_recommend_includes_score_explained() -> None:
    rec = recommend_for_score(
        {"composite": 0.61, "volatility_n": 0.5, "volume_n": 0.4, "liquidity_n": 0.4},
        profile="momentum",
        interval="1h",
    )
    assert "score_explained" in rec
    assert rec["score_explained"]["band"]["id"] == "good"
    assert rec["score_explained"]["family"] == "momentum"
