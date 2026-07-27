"""FASE 9 — observabilidad / cache / cancelacion."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from quantlab.core.types.market import Bar
from quantlab.research.alpha.observe import (
    CancellationToken,
    ScanCancelled,
    ScoreCache,
    run_observed_profile_scan,
)


def _bars(sym: str, n: int = 12) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(100 + i)
        t0 = base + timedelta(hours=i)
        out.append(
            Bar(
                instrument_id=f"BN:{sym}",
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


def test_observed_scan_emits_progress_and_metrics() -> None:
    bars = {"BN:A": _bars("A"), "BN:B": _bars("B")}
    events: list[str] = []
    result = run_observed_profile_scan(
        bars,
        "legacy_v1",
        cache_key=None,
        use_cache=False,
        on_progress=lambda e: events.append(e.stage),
    )
    assert "start" in events
    assert "done" in events
    assert result.metrics.duration_ms is not None
    assert result.metrics.n_instruments == 2
    assert result.metrics.cache_hit is False


def test_score_cache_hit() -> None:
    bars = {"BN:A": _bars("A"), "BN:B": _bars("B")}
    cache = ScoreCache(ttl_seconds=30.0)
    key = "test-key"
    r1 = run_observed_profile_scan(
        bars, "momentum", cache_key=key, cache=cache, use_cache=True
    )
    assert r1.metrics.cache_hit is False
    r2 = run_observed_profile_scan(
        bars, "momentum", cache_key=key, cache=cache, use_cache=True
    )
    assert r2.metrics.cache_hit is True
    assert len(r1.rows) == len(r2.rows)


def test_cancellation_before_score() -> None:
    bars = {"BN:A": _bars("A")}
    token = CancellationToken()
    token.cancel()
    with pytest.raises(ScanCancelled):
        run_observed_profile_scan(
            bars, "legacy_v1", token=token, use_cache=False
        )
