"""Tests Alpha Scanner Fase 4."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.research.alpha import AlphaScanner, GapPolicy


def _bars(instrument: str, closes: list[str], volumes: list[str]) -> list[Bar]:
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i, (c, v) in enumerate(zip(closes, volumes, strict=True)):
        px = Decimal(c)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id=instrument,
                open=px,
                high=px + Decimal("0.5"),
                low=px - Decimal("0.5"),
                close=px,
                volume=Decimal(v),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def test_scanner_ranks_deterministically() -> None:
    data = {
        "A": _bars("A", ["10", "11", "12", "13"], ["10", "10", "10", "10"]),
        "B": _bars("B", ["10", "10.1", "10.05", "10.02"], ["1000", "1000", "1000", "1000"]),
        "C": _bars("C", ["5", "8", "4", "9"], ["50", "50", "50", "50"]),
    }
    scanner = AlphaScanner()
    r1 = scanner.scan(data, top_n=2)
    r2 = scanner.scan(data, top_n=2)
    assert r1.selected == r2.selected
    assert len(r1.selected) == 2
    assert len(r1.scores) == 3
    assert r1.scores[0].composite >= r1.scores[1].composite


def test_scanner_handles_bar_gaps_forward_fill() -> None:
    base = datetime(2024, 6, 1, tzinfo=UTC)
    bars = _bars("G", ["10", "11", "12"], ["1", "1", "1"])
    # Insertar hueco grande en el último close
    gapped = [
        bars[0],
        bars[1],
        Bar(
            instrument_id="G",
            open=Decimal("12"),
            high=Decimal("12.5"),
            low=Decimal("11.5"),
            close=Decimal("12"),
            volume=Decimal("1"),
            timestamp_open=base + timedelta(minutes=10),
            timestamp_close=base + timedelta(minutes=11),
            timeframe="1m",
        ),
    ]
    scanner = AlphaScanner(gap_policy=GapPolicy.FORWARD_FILL)
    result = scanner.scan({"G": gapped}, top_n=1, min_bars=3)
    assert result.selected == ("G",)
    assert result.gap_events
    assert any("bar_gap" in e for e in result.gap_events)


def test_scanner_volatility_ignores_synthetic_zero_volume() -> None:
    """TD-11: forward-fill no debe aplanar volatilidad vía closes sintéticos."""
    base = datetime(2024, 6, 1, tzinfo=UTC)

    def bar(close: str, minutes: int, vol: str = "100") -> Bar:
        px = Decimal(close)
        t0 = base + timedelta(minutes=minutes)
        return Bar(
            instrument_id="V",
            open=px,
            high=px + Decimal("0.5"),
            low=px - Decimal("0.5"),
            close=px,
            volume=Decimal(vol),
            timestamp_open=t0,
            timestamp_close=t0 + timedelta(minutes=1),
            timeframe="1m",
        )

    # delta 1m (primeras dos) + hueco → sintéticas vol=0; live con retornos fuertes
    live = [bar("10", 0), bar("11", 1), bar("20", 10), bar("8", 11)]
    result = AlphaScanner(gap_policy=GapPolicy.FORWARD_FILL).scan({"V": live}, top_n=1, min_bars=3)
    assert result.scores
    assert result.gap_events
    # Solo closes live → pstdev de retornos grandes; sintéticas no aplanan
    assert result.scores[0].volatility > 0.1
