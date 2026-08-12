"""Export scanner individual → AlphaSignal (paridad de contrato con pares)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from quantlab.research.alpha.models import (
    AlphaSignal,
    SignalDirection,
    SignalScope,
)
from quantlab.research.alpha.normalization import percentile_rank_signals
from quantlab.research.alpha.signals import stable_signal_id
from quantlab.research.alpha.validation.pipeline import ValidationPipeline


def _factor_coverage(row: Mapping[str, Any]) -> float:
    """confidence simple: fracción de componentes disponibles (0–1)."""
    comps = row.get("components")
    if isinstance(comps, list) and comps:
        avail = sum(
            1
            for c in comps
            if isinstance(c, Mapping)
            and c.get("available") is not False
            and c.get("raw") is not None
        )
        return round(avail / max(1, len(comps)), 4)
    # legacy AssetScore: tres factores
    keys = ("volatility", "volume_score", "liquidity_score")
    present = sum(1 for k in keys if row.get(k) is not None)
    if present:
        return round(present / len(keys), 4)
    return 0.5


def score_row_to_signal(
    row: Mapping[str, Any],
    *,
    signal_type: str,
    timeframe: str,
    lookback: int,
    timestamp: datetime | None = None,
) -> AlphaSignal:
    ts = timestamp or datetime.now(tz=UTC)
    iid = str(row.get("instrument_id") or row.get("normalized_instrument") or "")
    if not iid:
        sym = str(row.get("symbol") or "")
        iid = sym
    composite = row.get("composite")
    if composite is not None:
        raw = float(composite)
    else:
        raw_score = row.get("raw_score")
        raw = float(raw_score if raw_score is not None else 0.0)
    conf = _factor_coverage(row)
    return AlphaSignal(
        signal_id=stable_signal_id(
            signal_type=signal_type,
            scope=SignalScope.INDIVIDUAL,
            symbols=(iid,),
            timestamp=ts,
            raw_score=raw,
            lag=None,
            lookback=lookback,
        ),
        timestamp=ts,
        signal_type=signal_type,
        scope=SignalScope.INDIVIDUAL,
        symbols=(iid,),
        direction=SignalDirection.LONG,
        raw_score=raw,
        confidence=conf,
        lookback=lookback,
        timeframe=timeframe,
        metadata={
            "base_score": row.get("base_score"),
            "symbol": row.get("symbol"),
            "underlying": row.get("underlying"),
            "rank_source": "individual_scanner",
        },
    )


def scores_to_ranked_signals(
    scores: Sequence[Mapping[str, Any]],
    *,
    profile: str,
    timeframe: str,
    lookback: int = 0,
) -> tuple[AlphaSignal, ...]:
    pipe = ValidationPipeline()
    ts = datetime.now(tz=UTC)
    raw_sigs: list[AlphaSignal] = []
    for row in scores:
        if not isinstance(row, Mapping):
            continue
        if row.get("excluded") is True:
            continue
        pipe.assert_no_selection_leakage(selection_scores=dict(row))
        raw_sigs.append(
            score_row_to_signal(
                row,
                signal_type=profile or "legacy_v1",
                timeframe=timeframe,
                lookback=lookback,
                timestamp=ts,
            )
        )
    ranked = percentile_rank_signals(tuple(raw_sigs))
    return tuple(sorted(ranked, key=lambda s: s.normalized_score or 0.0, reverse=True))


def attach_individual_signals(
    payload: dict[str, Any],
    *,
    lookback: int | None = None,
) -> dict[str, Any]:
    """Añade ``signals[]`` AlphaSignal al payload del scanner individual."""
    scores = payload.get("scores") or []
    if not isinstance(scores, list):
        return payload
    profile = str(payload.get("profile") or "legacy_v1")
    timeframe = str(payload.get("interval") or "1h")
    lb = lookback if lookback is not None else int(payload.get("kline_limit") or 0)
    ranked = scores_to_ranked_signals(
        [s for s in scores if isinstance(s, Mapping)],
        profile=profile,
        timeframe=timeframe,
        lookback=lb,
    )
    top_n = int(payload.get("top_n") or len(ranked))
    top = ranked[: max(0, top_n)]
    payload["signals"] = [s.to_dict() for s in top]
    payload["signal_scope"] = "individual"
    note = str(payload.get("note") or "")
    extra = (
        " signals[] = AlphaSignal (scope=individual); "
        "ranking A = score de mercado, no backtest."
    )
    if extra.strip() not in note:
        payload["note"] = (note + extra).strip()
    return payload


__all__ = [
    "attach_individual_signals",
    "score_row_to_signal",
    "scores_to_ranked_signals",
]
