"""IP-1 — DetectorRegistry."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.research.alpha.detectors.base import DetectorContext, DetectorRunConfig
from quantlab.research.alpha.detectors.registry import DetectorRegistry
from quantlab.research.alpha.models import AlphaSignal, SignalDirection, SignalScope


class _DummyDetector:
    @property
    def detector_id(self) -> str:
        return "dummy"

    @property
    def signal_type(self) -> str:
        return "dummy"

    @property
    def scope(self) -> SignalScope:
        return SignalScope.INDIVIDUAL

    def required_min_bars(self) -> int:
        return 1

    def detect(self, ctx: DetectorContext) -> tuple[AlphaSignal, ...]:
        ts = datetime(2026, 8, 12, tzinfo=UTC)
        out: list[AlphaSignal] = []
        for iid in ctx.bars_by_instrument:
            out.append(
                AlphaSignal(
                    signal_id=f"dummy-{iid}",
                    timestamp=ts,
                    signal_type="dummy",
                    scope=SignalScope.INDIVIDUAL,
                    symbols=(iid,),
                    direction=SignalDirection.NEUTRAL,
                    raw_score=1.0,
                )
            )
        return tuple(out)


def test_registry_register_and_run() -> None:
    reg = DetectorRegistry()
    det = _DummyDetector()
    reg.register(det)
    assert reg.list_ids() == ("dummy",)
    bar = Bar(
        instrument_id="WB:A",
        timestamp_open=datetime(2026, 1, 1, tzinfo=UTC),
        timestamp_close=datetime(2026, 1, 1, 1, tzinfo=UTC),
        open=Decimal("1"),
        high=Decimal("1"),
        low=Decimal("1"),
        close=Decimal("1"),
        volume=Decimal("1"),
        timeframe="1h",
    )
    ctx = DetectorContext(
        bars_by_instrument={"WB:A": (bar,)},
        timeframe="1h",
        lookback_bars=16,
        venue="lab",
        market_type="synthetic",
    )
    signals = reg.run_all(ctx, DetectorRunConfig(enabled=("dummy",)))
    assert len(signals) == 1
    assert signals[0].symbols == ("WB:A",)


def test_registry_unknown_detector_raises() -> None:
    reg = DetectorRegistry()
    ctx = DetectorContext(
        bars_by_instrument={},
        timeframe="1h",
        lookback_bars=16,
        venue="lab",
        market_type="synthetic",
    )
    try:
        reg.run_all(ctx, DetectorRunConfig(enabled=("missing",)))
        raise AssertionError("expected ValidationError")
    except Exception as exc:
        assert "desconocido" in str(exc).lower()
