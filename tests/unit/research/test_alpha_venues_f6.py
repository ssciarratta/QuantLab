"""FASE 6 — multi-venue capabilities + ranking combinado."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.types.market import Bar
from quantlab.research.alpha.venues import (
    VENUE_BINANCE,
    VENUE_HYPERLIQUID,
    assert_venue_fetchable,
    build_venue_slice,
    get_venue_capabilities,
    list_venue_capabilities,
    scan_multi_venue,
)


def _bars(prefix: str, sym: str, n: int = 16) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"{prefix}{sym}",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("0.5"),
                close=c,
                volume=Decimal("1000"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


def test_capability_catalog_includes_four_venues() -> None:
    caps = {c.venue: c for c in list_venue_capabilities()}
    assert VENUE_BINANCE in caps
    assert VENUE_HYPERLIQUID in caps
    assert caps[VENUE_BINANCE].fetch_implemented is True
    assert caps[VENUE_HYPERLIQUID].fetch_implemented is False


def test_assert_venue_fetchable_blocks_unimplemented() -> None:
    assert_venue_fetchable(VENUE_BINANCE)
    with pytest.raises(NotImplementedError, match="fetch"):
        assert_venue_fetchable(VENUE_HYPERLIQUID)


def test_combined_ranking_two_venues() -> None:
    bn = build_venue_slice(
        venue=VENUE_BINANCE,
        symbols=["AAA", "BBB"],
        bars_by_symbol={"AAA": _bars("BN:", "AAA"), "BBB": _bars("BN:", "BBB")},
        instrument_prefix="BN:",
    )
    # Lab sinteticos con prefix distinto
    lab = build_venue_slice(
        venue="lab",
        symbols=["X"],
        bars_by_symbol={"X": _bars("WB:", "X")},
        instrument_prefix="WB:",
    )
    result = scan_multi_venue([bn, lab], profile="legacy_v1")
    ids = {r.instrument_id for r in result.rows if not r.excluded}
    assert ids == {"BN:AAA", "BN:BBB", "WB:X"}


def test_unimplemented_venue_omitted_with_warning() -> None:
    bn = build_venue_slice(
        venue=VENUE_BINANCE,
        symbols=["AAA"],
        bars_by_symbol={"AAA": _bars("BN:", "AAA")},
        instrument_prefix="BN:",
    )
    hl = build_venue_slice(
        venue=VENUE_HYPERLIQUID,
        symbols=["ETH"],
        bars_by_symbol={"ETH": _bars("HL:", "ETH")},
        instrument_prefix="HL:",
    )
    # Marcar slice con caps reales (fetch false)
    assert hl.capabilities.fetch_implemented is False
    result = scan_multi_venue([bn, hl], profile="momentum")
    assert any("hyperliquid" in w for w in result.warnings)
    ids = {r.instrument_id for r in result.rows if not r.excluded}
    assert ids == {"BN:AAA"}


def test_unknown_venue_raises() -> None:
    with pytest.raises(ValueError, match="desconocido"):
        get_venue_capabilities("kraken")
