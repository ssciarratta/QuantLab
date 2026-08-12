"""Percentile ranking transversal para AlphaSignal (pairwise + individual)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from quantlab.research.alpha.models import AlphaSignal


def _group_key(sig: AlphaSignal, keys: tuple[str, ...]) -> tuple[str, ...]:
    parts: list[str] = []
    d = sig.to_dict()
    for k in keys:
        if k == "timestamp":
            parts.append(str(sig.timestamp.date()))
        else:
            parts.append(str(d.get(k, "")))
    return tuple(parts)


def percentile_rank_signals(
    signals: Sequence[AlphaSignal],
    *,
    group_by: tuple[str, ...] = ("timestamp", "timeframe", "scope", "signal_type"),
) -> tuple[AlphaSignal, ...]:
    """Asigna ``normalized_score`` ∈ [0,1] por grupo (sin mezclar scope/TF/fecha)."""
    if not signals:
        return ()
    buckets: dict[tuple[str, ...], list[AlphaSignal]] = defaultdict(list)
    for sig in signals:
        buckets[_group_key(sig, group_by)].append(sig)

    out: list[AlphaSignal] = []
    for _key, group in buckets.items():
        scores = [s.raw_score for s in group]
        lo, hi = min(scores), max(scores)
        span = hi - lo
        ranked = sorted(group, key=lambda s: s.raw_score)
        n = len(ranked)
        for i, sig in enumerate(ranked):
            if span <= 0:
                pct = 0.5 if n == 1 else i / max(1, n - 1)
            else:
                pct = (sig.raw_score - lo) / span
            out.append(
                AlphaSignal(
                    signal_id=sig.signal_id,
                    timestamp=sig.timestamp,
                    signal_type=sig.signal_type,
                    scope=sig.scope,
                    symbols=sig.symbols,
                    direction=sig.direction,
                    raw_score=sig.raw_score,
                    confidence=sig.confidence,
                    lookback=sig.lookback,
                    lag=sig.lag,
                    timeframe=sig.timeframe,
                    data_quality=sig.data_quality,
                    metadata=sig.metadata,
                    normalized_score=round(pct, 8),
                )
            )
    return tuple(out)


__all__ = ["percentile_rank_signals"]
