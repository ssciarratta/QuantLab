"""TD-06 — explicabilidad AlphaScanner con contribución normalizada exacta."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.research.alpha import AlphaScanner
from quantlab.research.alpha.explain import explain_scores


def _bars(instrument_id: str, closes: tuple[str, ...], volume: str) -> list[Bar]:
    base = datetime(2024, 6, 1, tzinfo=UTC)
    out: list[Bar] = []
    for i, c in enumerate(closes):
        px = Decimal(c)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id=instrument_id,
                open=px,
                high=px + Decimal("0.5"),
                low=px - Decimal("0.5"),
                close=px,
                volume=Decimal(volume),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_explain_includes_weighted_contribution() -> None:
    # Dos activos → normalización cross-section ≠ trivial
    result = AlphaScanner().scan(
        {
            "A": _bars("A", ("10", "11", "12", "13"), "10"),
            "B": _bars("B", ("10", "10.1", "10.2", "10.3"), "100"),
        },
        top_n=2,
    )
    expl = explain_scores(result, top=2)
    assert len(expl) == 2
    for item in expl:
        joined = " | ".join(item.drivers)
        assert "contrib=" in joined
        assert "share=" in joined
        assert "w=" in joined
        assert abs(item.contrib_sum - item.composite) < 1e-6
