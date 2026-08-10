"""Tests: diagnóstico score degradado / empatados en 0."""

from __future__ import annotations

from quantlab.research.alpha.scan_quality import assess_scan_quality, attach_scan_quality


def _row(composite: float, *, factors: dict[str, float] | None = None) -> dict:
    comps = []
    for name, raw in (factors or {"liquidity": 1.0, "spread": 0.0}).items():
        comps.append(
            {
                "name": name,
                "raw": raw,
                "normalized": 0.0,
                "weight": 0.25,
                "contribution": 0.0,
                "available": True,
            }
        )
    return {"instrument_id": "x", "composite": composite, "components": comps}


def test_all_zero_composites_degraded() -> None:
    out = {
        "profile": "market_making",
        "scores": [
            _row(0.0, factors={"liquidity": 10.0, "spread": 0.0, "volume": 1.0}),
            _row(0.0, factors={"liquidity": 10.0, "spread": 0.0, "volume": 1.0}),
            _row(0.0, factors={"liquidity": 10.0, "spread": 0.0, "volume": 1.0}),
        ],
    }
    assessed = assess_scan_quality(out, md_meta={"provider": "a3-fake"})
    assert assessed["score_status"] == "degraded"
    assert assessed["score_reason"] == "zero_cross_section_variance"
    assert any("0.000" in w or "scores = 0" in w for w in assessed["warnings"])
    assert any("fake" in w.lower() for w in assessed["warnings"])
    attach_scan_quality(out, md_meta={"provider": "a3-fake"})
    assert out["scores"][0]["score_status"] == "tied_zero"
    assert "liquidity" in (out.get("tied_factors") or [])


def test_ok_when_scores_differ() -> None:
    out = {
        "profile": "trend",
        "scores": [
            _row(0.9, factors={"momentum": 0.9}),
            _row(0.4, factors={"momentum": 0.2}),
        ],
    }
    assessed = assess_scan_quality(out)
    assert assessed["score_status"] == "ok"
    assert assessed["warnings"] == []


def test_fetch_failures_partial() -> None:
    out = {"profile": "trend", "scores": [_row(0.5), _row(0.3)]}
    assessed = assess_scan_quality(
        out, fetch_failures={"FOO": "timeout", "BAR": "sin barras"}
    )
    assert assessed["score_status"] == "partial"
    assert any("sin datos MD" in w for w in assessed["warnings"])
