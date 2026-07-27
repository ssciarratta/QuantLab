"""Walk-forward helpers: ranking window ≠ backtest window (anti in-sample)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from quantlab.core.types.market import Bar


@dataclass(frozen=True, slots=True)
class WalkForwardSplit:
    """Partición temporal determinista sobre barras ordenadas por timestamp."""

    rank_bars: dict[str, list[Bar]]
    backtest_bars: dict[str, list[Bar]]
    rank_fraction: float
    n_rank: int
    n_backtest: int
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank_fraction": self.rank_fraction,
            "n_rank": self.n_rank,
            "n_backtest": self.n_backtest,
            "n_instruments_rank": len(self.rank_bars),
            "n_instruments_backtest": len(self.backtest_bars),
            "note": self.note,
        }


def split_bars_walk_forward(
    bars_by_instrument: Mapping[str, Sequence[Bar]],
    *,
    rank_fraction: float = 0.70,
    min_rank_bars: int = 8,
    min_backtest_bars: int = 8,
) -> WalkForwardSplit:
    """Primera fracción → ranking; resto → backtest (sin overlap temporal).

    Asume barras ordenadas ASC por ``timestamp_close``. Misma longitud ideal
    por instrumento; si difiere, corta por longitud de cada serie.
    """
    if not (0.05 <= rank_fraction <= 0.95):
        raise ValueError(f"rank_fraction fuera de [0.05, 0.95]: {rank_fraction}")

    rank_out: dict[str, list[Bar]] = {}
    bt_out: dict[str, list[Bar]] = {}
    n_rank = 0
    n_bt = 0

    for iid, bars in bars_by_instrument.items():
        seq = list(bars)
        n = len(seq)
        if n < min_rank_bars + min_backtest_bars:
            continue
        cut = int(n * rank_fraction)
        cut = max(min_rank_bars, min(cut, n - min_backtest_bars))
        rank_part = seq[:cut]
        bt_part = seq[cut:]
        if len(rank_part) < min_rank_bars or len(bt_part) < min_backtest_bars:
            continue
        rank_out[iid] = rank_part
        bt_out[iid] = bt_part
        n_rank = len(rank_part)
        n_bt = len(bt_part)

    if not rank_out or not bt_out:
        raise ValueError(
            "walk-forward: insuficiente historia "
            f"(min_rank={min_rank_bars}, min_bt={min_backtest_bars})"
        )

    note = (
        f"Ranking usa las primeras ~{rank_fraction:.0%} barras; "
        "backtest usa el tramo posterior (sin overlap). "
        "Reduce selección in-sample; no garantiza rentabilidad OOS."
    )
    return WalkForwardSplit(
        rank_bars=rank_out,
        backtest_bars=bt_out,
        rank_fraction=rank_fraction,
        n_rank=n_rank,
        n_backtest=n_bt,
        note=note,
    )


__all__ = ["WalkForwardSplit", "split_bars_walk_forward"]
