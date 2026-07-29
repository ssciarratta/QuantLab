"""Tests unitarios: recomendaciones Alpha Scanner (sin red)."""

from __future__ import annotations

from quantlab.research.alpha.recommend import (
    PROFILE_AUTO,
    SCORING_PROFILE_AUTO,
    attach_recommendations,
    build_auto_proposal,
    infer_family,
    is_auto_profile,
    recommend_for_score,
    recommend_timeframes,
    resolve_scoring_profile,
    strategies_for_family,
    underlying_from_symbol,
)


def test_underlying_from_symbol() -> None:
    assert underlying_from_symbol("BTCUSDT") == "BTC"
    assert underlying_from_symbol("BTC-USDT-SWAP") == "BTC"
    assert underlying_from_symbol("BN:ETHUSDT") == "ETH"
    assert underlying_from_symbol("xyz:GOLD") == "xyz:GOLD"


def test_infer_family_from_profile() -> None:
    row = {"volatility_n": 0.2, "volume_n": 0.2, "liquidity_n": 0.2}
    assert infer_family(row, profile="momentum") == "momentum"
    assert infer_family(row, profile="mean_reversion") == "mean_reversion"
    assert infer_family(row, profile="market_making") == "market_making"
    assert infer_family(row, profile="trend") == "trend"
    assert infer_family(row, profile="options") == "options"
    assert infer_family(row, profile="ml") == "ml"


def test_infer_family_from_score_heuristic() -> None:
    high_mom = {
        "volatility_n": 0.5,
        "volume_n": 0.4,
        "liquidity_n": 0.4,
        "components": [
            {"name": "momentum", "normalized": 0.9},
            {"name": "trend_quality", "normalized": 0.8},
        ],
    }
    assert infer_family(high_mom, profile="legacy_v1") == "momentum"

    high_vol = {
        "volatility_n": 0.85,
        "volume_n": 0.3,
        "liquidity_n": 0.3,
        "components": [{"name": "momentum", "normalized": 0.2}],
    }
    assert infer_family(high_vol, profile="legacy_v1") == "mean_reversion"


def test_strategies_for_family_prefers_runnable() -> None:
    rows = strategies_for_family("momentum", limit=3)
    assert 1 <= len(rows) <= 3
    assert all("id" in r and "name" in r for r in rows)
    # primer runnable si existe alguno
    if any(r["runnable"] for r in rows):
        assert rows[0]["runnable"] is True


def test_recommend_timeframes_includes_current() -> None:
    tfs = recommend_timeframes("1h", {"volatility_n": 0.5})
    assert tfs[0]["interval"] == "1h"
    assert tfs[0]["primary"] is True
    assert len(tfs) >= 3


def test_recommend_for_score_shape() -> None:
    rec = recommend_for_score(
        {
            "composite": 0.77,
            "volatility_n": 0.6,
            "volume_n": 0.5,
            "liquidity_n": 0.4,
        },
        profile="momentum",
        interval="4h",
    )
    assert rec["family"] == "momentum"
    assert rec["family_label_es"]
    assert len(rec["strategies"]) >= 1
    assert len(rec["timeframes"]) >= 1
    assert "Score" in rec["text"]


def test_attach_recommendations_enriches_scores() -> None:
    out = attach_recommendations(
        {
            "profile": "legacy_v1",
            "interval": "1h",
            "scores": [
                {
                    "instrument_id": "BN:BTCUSDT",
                    "composite": 0.9,
                    "volatility_n": 0.4,
                    "volume_n": 0.5,
                    "liquidity_n": 0.6,
                }
            ],
        }
    )
    assert "recommendation" in out["scores"][0]
    assert out["scores"][0]["underlying"] == "BTC"
    assert "recommendations" in out
    assert out["recommendations"]["family"]


def test_is_auto_profile_and_resolve() -> None:
    assert is_auto_profile("auto")
    assert is_auto_profile("")
    assert is_auto_profile(None)
    assert not is_auto_profile("trend")
    requested, scoring, auto = resolve_scoring_profile("auto")
    assert requested == PROFILE_AUTO
    assert scoring == SCORING_PROFILE_AUTO
    assert auto is True
    requested2, scoring2, auto2 = resolve_scoring_profile("momentum")
    assert requested2 == "momentum"
    assert scoring2 == "momentum"
    assert auto2 is False


def test_attach_recommendations_auto_adds_proposal() -> None:
    out = attach_recommendations(
        {
            "profile": "auto",
            "interval": "1h",
            "top_n": 3,
            "venue": "binance",
            "scores": [
                {
                    "instrument_id": "BN:BTCUSDT",
                    "symbol": "BTCUSDT",
                    "composite": 0.9,
                    "volatility_n": 0.5,
                    "volume_n": 0.5,
                    "liquidity_n": 0.5,
                    "components": [
                        {"name": "momentum", "normalized": 0.9},
                        {"name": "trend_quality", "normalized": 0.85},
                    ],
                },
                {
                    "instrument_id": "BN:ETHUSDT",
                    "symbol": "ETHUSDT",
                    "composite": 0.8,
                    "volatility_n": 0.5,
                    "volume_n": 0.4,
                    "liquidity_n": 0.4,
                    "components": [
                        {"name": "momentum", "normalized": 0.88},
                        {"name": "trend_quality", "normalized": 0.8},
                    ],
                },
            ],
        },
        profile="auto",
    )
    assert out["auto_mode"] is True
    assert out["profile"] == PROFILE_AUTO
    assert out["scoring_profile"] == SCORING_PROFILE_AUTO
    assert "proposal" in out
    prop = out["proposal"]
    assert prop["auto_mode"] is True
    assert prop["family"]
    assert len(prop["strategies"]) >= 1
    assert len(prop["timeframes"]) >= 1
    assert out["scores"][0]["recommendation"]["auto_mode"] is True


def test_build_auto_proposal_majority_family() -> None:
    scores = [
        {
            "underlying": "BTC",
            "recommendation": {
                "family": "momentum",
                "strategies": [{"id": "m1", "name": "M1", "runnable": True}],
                "timeframes": [{"interval": "1h", "primary": True}],
            },
        },
        {
            "underlying": "ETH",
            "recommendation": {
                "family": "momentum",
                "strategies": [{"id": "m1", "name": "M1", "runnable": True}],
                "timeframes": [{"interval": "1h", "primary": True}],
            },
        },
        {
            "underlying": "SOL",
            "recommendation": {
                "family": "trend",
                "strategies": [{"id": "t1", "name": "T1", "runnable": True}],
                "timeframes": [{"interval": "4h", "primary": True}],
            },
        },
    ]
    prop = build_auto_proposal(scores, interval="1h", venue="okx", top_n=3)
    assert prop["family"] == "momentum"
    assert prop["venue"] == "okx"
    assert prop["votes"]["momentum"] == 2
