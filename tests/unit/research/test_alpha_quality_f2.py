"""FASE 2 — calidad de datos y universo con exclusiones tipadas."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.research.alpha.quality import (
    EligibilityConfig,
    ExclusionReason,
    assess_bar_quality,
    evaluate_eligibility,
)
from quantlab.research.alpha.universe import build_universe_from_symbol_bars
from quantlab.workbench import lab_services


def _bars(sym: str, n: int = 24, *, bad_price: bool = False) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal("0") if bad_price and i == 0 else Decimal(100 + i)
        # require_positive on Bar — bad price via evaluate with empty instead
        if c <= 0:
            c = Decimal("0.0000001")
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"BN:{sym}",
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("0.5") if c > 1 else c,
                close=c,
                volume=Decimal("1000"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(hours=1),
                timeframe="1h",
            )
        )
    return out


def test_quality_report_never_fakes_optional_as_zero() -> None:
    bars = _bars("AAA", 10)
    q = assess_bar_quality("BN:AAA", bars, expected_bars=10)
    assert q.candles_available is True
    assert q.ticker_available is None
    assert q.funding_available is None
    assert q.open_interest_available is None
    assert q.completeness == 1.0
    assert q.valid_bars == 10


def test_eligibility_fetch_failed_is_typed() -> None:
    ev = evaluate_eligibility("BN:XYZ", None, fetch_failed=True, fetch_error="timeout")
    assert ev.eligible is False
    assert ExclusionReason.FETCH_FAILED in ev.reasons
    assert "timeout" in ev.detail


def test_eligibility_insufficient_history() -> None:
    bars = _bars("TINY", 2)
    ev = evaluate_eligibility(
        "BN:TINY", bars, config=EligibilityConfig(min_bars=8, min_completeness=0.0)
    )
    assert ev.eligible is False
    assert ExclusionReason.INSUFFICIENT_HISTORY in ev.reasons


def test_universe_records_missing_symbols() -> None:
    built = build_universe_from_symbol_bars(
        venue="binance",
        symbols=["AAA", "BBB", "CCC"],
        bars_by_symbol={"AAA": _bars("AAA", 20), "CCC": _bars("CCC", 20)},
        fetch_failures={"BBB": "klines omitidas o inválidas"},
        eligibility_config=EligibilityConfig(min_bars=3, min_completeness=0.5),
    )
    assert "BBB" in {e.symbol for e in built.exclusions}
    assert any("fetch_failed" in e.reasons for e in built.exclusions)
    assert set(built.eligible_bars.keys()) == {"BN:AAA", "BN:CCC"}


def test_binance_scanner_exposes_exclusions() -> None:
    from unittest.mock import patch

    uni = {
        "BTCUSDT": _bars("BTCUSDT", 24),
        "ETHUSDT": _bars("ETHUSDT", 24),
    }
    symbols = ["BTCUSDT", "ETHUSDT", "FAILUSDT"]
    with (
        patch(
            "quantlab.brokers.binance.public_md.BinancePublicMdClient.list_spot_symbols",
            return_value=symbols,
        ),
        patch(
            "quantlab.brokers.binance.public_md.fetch_universe_bars",
            return_value=uni,
        ),
    ):
        out = lab_services.run_binance_lab_scanner(top_n=2, symbol_limit=5, kline_limit=24)
    assert out["ok"] is True
    assert out["fetched"] == 3
    assert out["excluded"] >= 1
    assert any(e["symbol"] == "FAILUSDT" for e in out["exclusions"])
    assert "fetch_failed" in out["exclusion_counts"]
    assert "note" in out
