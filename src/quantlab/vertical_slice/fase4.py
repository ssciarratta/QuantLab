"""Vertical slice Fase 4: scanner → simulación → métricas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from quantlab.core.types.market import Bar
from quantlab.core.types.results import MetricsResult, SimulationResult
from quantlab.infra.logging import configure_logging, get_logger
from quantlab.metrics import MetricsEngine
from quantlab.research.alpha import AlphaScanner, ScannerResult
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.simulation import BarSimulationEngine, SimulationConfig

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Fase4SliceResult:
    scanner: ScannerResult
    simulation: SimulationResult
    metrics: MetricsResult


def _synthetic_universe() -> dict[str, list[Bar]]:
    base = datetime(2024, 3, 1, tzinfo=UTC)

    def make(iid: str, closes: list[str], vol: str) -> list[Bar]:
        bars: list[Bar] = []
        for i, c in enumerate(closes):
            px = Decimal(c)
            t0 = base + timedelta(minutes=i)
            bars.append(
                Bar(
                    instrument_id=iid,
                    open=px,
                    high=px + Decimal("1"),
                    low=px - Decimal("1"),
                    close=px,
                    volume=Decimal(vol),
                    timestamp_open=t0,
                    timestamp_close=t0 + timedelta(minutes=1),
                    timeframe="1m",
                )
            )
        return bars

    return {
        "ALPHA": make("ALPHA", ["100", "101", "102", "103", "104"], "500"),
        "BETA": make("BETA", ["50", "51", "49", "52", "50"], "50"),
        "GAMMA": make("GAMMA", ["10", "10.2", "10.1", "10.15", "10.12"], "2000"),
    }


def run_fase4_slice(*, experiment_id: str = "fase4-slice") -> Fase4SliceResult:
    from quantlab.infra.config.models import LoggingConfig

    configure_logging(LoggingConfig())
    universe = _synthetic_universe()
    scanner = AlphaScanner()
    scan = scanner.scan(universe, top_n=1)
    chosen = scan.selected[0]
    bars = universe[chosen]
    engine = BarSimulationEngine(
        SimulationConfig(experiment_id=experiment_id, initial_cash=Decimal("100000"))
    )
    sim = engine.run(BuyOnceStrategy({"quantity": "1"}), bars)
    metrics = MetricsEngine().compute(sim)
    logger.info(
        "fase4_slice_done",
        selected=chosen,
        sharpe=metrics.metrics.get("sharpe"),
        fills=len(sim.fills),
    )
    return Fase4SliceResult(scanner=scan, simulation=sim, metrics=metrics)


def main() -> None:
    result = run_fase4_slice()
    print(f"selected={result.scanner.selected}")
    print(f"fills={len(result.simulation.fills)}")
    print(f"metrics={dict(result.metrics.metrics)}")


if __name__ == "__main__":
    main()
