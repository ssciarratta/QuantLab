"""TD-06 — explicabilidad AlphaScanner con contribución ponderada."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.research.alpha import AlphaScanner
from quantlab.research.alpha.explain import explain_scores


def test_explain_includes_weighted_contribution() -> None:
    base = datetime(2024, 6, 1, tzinfo=UTC)
    bars = []
    for i, c in enumerate(("10", "11", "12", "13")):
        px = Decimal(c)
        t0 = base + timedelta(minutes=i)
        bars.append(
            Bar(
                instrument_id="E",
                open=px,
                high=px + Decimal("0.5"),
                low=px - Decimal("0.5"),
                close=px,
                volume=Decimal("10"),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    result = AlphaScanner().scan({"E": bars}, top_n=1)
    expl = explain_scores(result, top=1)
    assert len(expl) == 1
    assert expl[0].instrument_id == "E"
    joined = " | ".join(expl[0].drivers)
    assert "contrib≈" in joined
    assert "w=" in joined
