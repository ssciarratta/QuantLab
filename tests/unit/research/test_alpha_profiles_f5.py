"""FASE 5 — perfiles de scoring Alpha Scanner."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.types.market import Bar
from quantlab.research.alpha import AlphaScanner
from quantlab.research.alpha.features import MarketExtras
from quantlab.research.alpha.profiles import (
    PROFILE_FUNDING,
    PROFILE_LEGACY_V1,
    PROFILE_MOMENTUM,
    build_profile,
    list_profiles,
    score_with_profile,
)


def _bars(sym: str, n: int = 24, *, trend: bool = True, vol_mult: int = 1) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + (2 * i if trend else 0))
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"BN:{sym}",
                open=c,
                high=c + Decimal("2"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal(1000 * vol_mult),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


def test_catalog_has_expected_profiles() -> None:
    names = set(list_profiles())
    assert PROFILE_LEGACY_V1 in names
    assert PROFILE_MOMENTUM in names
    assert "balanced" in names
    assert len(names) >= 7
    for n in names:
        p = build_profile(n)
        assert p.factors
        assert abs(sum(f.weight for f in p.factors) - 1.0) < 1e-9
        d = p.to_dict()
        assert d["label_es"]
        assert d["name"] in d["label_es"] or d["label_es"].startswith(d["name"])


def test_profile_catalog_exposes_label_es() -> None:
    from quantlab.research.alpha.profiles import profile_catalog

    cat = profile_catalog()
    assert len(cat) >= 7
    assert all("label_es" in row and "description" in row for row in cat)
    legacy = next(r for r in cat if r["name"] == PROFILE_LEGACY_V1)
    assert "default lab" in legacy["label_es"]


def test_scanner_family_catalog_matches_simulator_branches() -> None:
    from quantlab.research.alpha.profiles import (
        SCANNER_FAMILY_ORDER,
        build_profile,
        scanner_family_catalog,
    )
    from quantlab.workbench.lab_services import list_alpha_profiles
    from quantlab.workbench.strategy_guides import FAMILY_LABELS_ES

    cat = scanner_family_catalog()
    assert len(cat) == 10
    assert [r["name"] for r in cat] == list(SCANNER_FAMILY_ORDER)
    assert "demo" not in {r["name"] for r in cat}
    for row in cat:
        assert row["label_es"] == FAMILY_LABELS_ES[row["name"]]
        assert row["family"] == row["name"]
        # Cada rama debe poder scorear
        assert build_profile(row["name"]).factors

    api = list_alpha_profiles()
    assert api["ok"] is True
    assert api["default_profile"] == "auto"
    assert len(api["profiles"]) == 11  # Auto + 10 familias
    assert api["profiles"][0]["name"] == "auto"
    assert api["profiles"][0]["auto_mode"] is True
    assert api["profiles"][1]["label_es"] == "Tendenciales"

def test_legacy_profile_matches_alpha_scanner() -> None:
    bars = {
        "BN:A": _bars("A", trend=True),
        "BN:B": _bars("B", trend=False, vol_mult=5),
    }
    legacy = AlphaScanner().scan(bars, top_n=2)
    rows = score_with_profile(bars, PROFILE_LEGACY_V1)
    by_l = {s.instrument_id: s.composite for s in legacy.scores}
    by_p = {r.instrument_id: r.composite for r in rows if not r.excluded}
    assert set(by_l) == set(by_p)
    for iid, c in by_l.items():
        assert by_p[iid] == pytest.approx(c, rel=1e-6, abs=1e-8)


def test_momentum_prefers_trending_symbol() -> None:
    bars = {
        "BN:TREND": _bars("TREND", trend=True),
        "BN:FLAT": _bars("FLAT", trend=False),
    }
    rows = [r for r in score_with_profile(bars, PROFILE_MOMENTUM) if not r.excluded]
    assert rows[0].instrument_id == "BN:TREND"


def test_funding_profile_renormalizes_without_faking_zero() -> None:
    bars = {"BN:A": _bars("A"), "BN:B": _bars("B", vol_mult=3)}
    # Sin extras → funding/OI None → renormaliza sobre volume/liquidity
    rows = score_with_profile(bars, PROFILE_FUNDING)
    assert all(not r.excluded for r in rows)
    for r in rows:
        funding_comp = next(c for c in r.components if c.name == "funding")
        assert funding_comp.available is False
        assert funding_comp.raw is None


def test_funding_uses_extras_when_present() -> None:
    bars = {"BN:A": _bars("A"), "BN:B": _bars("B")}
    extras = {
        "BN:A": MarketExtras(funding_rate=0.001, open_interest=1e6),
        "BN:B": MarketExtras(funding_rate=-0.0001, open_interest=2e6),
    }
    rows = score_with_profile(bars, PROFILE_FUNDING, extras_by_instrument=extras)
    assert any(
        c.available and c.name == "funding"
        for r in rows
        for c in r.components
    )


def test_unknown_profile_raises() -> None:
    with pytest.raises(ValueError, match="desconocido"):
        build_profile("no_existe")
