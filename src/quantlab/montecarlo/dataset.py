"""Referencia de dataset para corridas Monte Carlo trazables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from quantlab.core.types.market import Bar


@dataclass(frozen=True, slots=True)
class DatasetReference:
    """Identidad mínima de un dataset usado por MC."""

    dataset_id: str
    source: str
    venue: str | None
    network: str | None
    symbol: str | None
    normalized_instrument: str | None
    market_type: str | None
    timeframe: str
    start_time: datetime | None
    end_time: datetime | None
    bars: int
    hash: str
    storage_path: str | None = None
    synthetic: bool = False
    generator_config: dict[str, Any] | None = None
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source": self.source,
            "venue": self.venue,
            "network": self.network,
            "symbol": self.symbol,
            "normalized_instrument": self.normalized_instrument,
            "market_type": self.market_type,
            "timeframe": self.timeframe,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "bars": self.bars,
            "hash": self.hash,
            "storage_path": self.storage_path,
            "synthetic": self.synthetic,
            "generator_config": self.generator_config,
            "seed": self.seed,
            "duration_label": _duration_label(self.bars, self.timeframe),
            "label_es": (
                f"{self.bars} velas · {self.timeframe} · "
                f"{'sintético' if self.synthetic else self.source}"
            ),
        }

    @classmethod
    def from_synthetic_bars(
        cls,
        bars: Sequence[Bar],
        *,
        dataset_hash: str,
        generator_version: str = "make_synthetic_bars.v1",
        seed: int | None = None,
        start_price: int = 100,
        drift: int = 1,
    ) -> DatasetReference:
        if not bars:
            raise ValueError("bars vacío")
        first = bars[0]
        last = bars[-1]
        return cls(
            dataset_id="wb-synthetic",
            source="synthetic_lab",
            venue="lab",
            network="local",
            symbol=first.instrument_id,
            normalized_instrument=first.instrument_id,
            market_type="synthetic_spot",
            timeframe=first.timeframe or "1m",
            start_time=first.timestamp_open,
            end_time=last.timestamp_close,
            bars=len(bars),
            hash=dataset_hash,
            storage_path=None,
            synthetic=True,
            generator_config={
                "generator": "quantlab.workbench.lab_services.make_synthetic_bars",
                "version": generator_version,
                "start_price": start_price,
                "drift": drift,
                "instrument_id": first.instrument_id,
            },
            seed=seed,
        )


def _duration_label(n_bars: int, timeframe: str) -> str | None:
    tf = timeframe.strip().lower()
    if tf.endswith("m") and tf[:-1].isdigit():
        minutes = int(tf[:-1]) * n_bars
        if minutes < 60:
            return f"{minutes} min"
        hours = minutes / 60.0
        return f"{hours:.1f} h".replace(".0 h", " h")
    if tf.endswith("h") and tf[:-1].isdigit():
        return f"{int(tf[:-1]) * n_bars} h"
    if tf.endswith("d") and tf[:-1].isdigit():
        return f"{int(tf[:-1]) * n_bars} d"
    return None
