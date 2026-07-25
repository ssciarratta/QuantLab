"""Alpha Scanner — ranking determinista de activos (Fase 4)."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import timedelta
from enum import StrEnum
from statistics import mean, median, pstdev

from quantlab.core.types.market import Bar

logger = logging.getLogger(__name__)


class GapPolicy(StrEnum):
    """Política ante huecos de barras en el universo."""

    FORWARD_FILL = "forward_fill"
    DROP = "drop"


@dataclass(frozen=True, slots=True)
class AssetScore:
    instrument_id: str
    volatility: float
    volume_score: float
    liquidity_score: float
    composite: float
    # Componentes normalizados usados en composite (TD-06 explain exacto)
    volatility_n: float = 0.0
    volume_n: float = 0.0
    liquidity_n: float = 0.0


@dataclass(frozen=True, slots=True)
class ScannerResult:
    scores: tuple[AssetScore, ...]
    selected: tuple[str, ...]
    schema_version: str = "1.0"
    gap_events: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScannerWeights:
    volatility: float = 0.35
    volume: float = 0.35
    liquidity: float = 0.30


def _detect_bar_delta(bars: Sequence[Bar]) -> timedelta | None:
    if len(bars) < 2:
        return None
    seconds = [
        (bars[i].timestamp_close - bars[i - 1].timestamp_close).total_seconds()
        for i in range(1, len(bars))
    ]
    positives = [s for s in seconds if s > 0]
    if not positives:
        return None
    return timedelta(seconds=float(median(positives)))


def align_bars_for_gaps(
    bars: Sequence[Bar],
    *,
    policy: GapPolicy = GapPolicy.FORWARD_FILL,
    gap_factor: float = 1.5,
) -> tuple[list[Bar], list[str]]:
    """Detecta huecos; forward-fill declarativo o descarte seguro con log."""
    if len(bars) < 2:
        return list(bars), []
    delta = _detect_bar_delta(bars)
    if delta is None:
        return list(bars), []
    threshold = timedelta(seconds=delta.total_seconds() * gap_factor)
    out: list[Bar] = [bars[0]]
    events: list[str] = []
    for bar in bars[1:]:
        prev = out[-1]
        gap = bar.timestamp_close - prev.timestamp_close
        if gap > threshold:
            msg = (
                f"bar_gap instrument={bar.instrument_id} "
                f"from={prev.timestamp_close.isoformat()} "
                f"to={bar.timestamp_close.isoformat()} policy={policy.value}"
            )
            events.append(msg)
            logger.warning(msg)
            if policy is GapPolicy.DROP:
                # Descarte seguro: omitir la barra posterior al hueco
                continue
            # FORWARD_FILL: insertar barra sintética con OHLC del prev y volumen 0
            fill_ts_open = prev.timestamp_close
            fill_ts_close = prev.timestamp_close + delta
            while fill_ts_close < bar.timestamp_close:
                synthetic = replace(
                    prev,
                    open=prev.close,
                    high=prev.close,
                    low=prev.close,
                    close=prev.close,
                    volume=prev.volume * 0,
                    timestamp_open=fill_ts_open,
                    timestamp_close=fill_ts_close,
                )
                out.append(synthetic)
                fill_ts_open = fill_ts_close
                fill_ts_close = fill_ts_close + delta
                if len(out) > len(bars) * 20:
                    # guardrail anti-explosión
                    break
        out.append(bar)
    return out, events


class AlphaScanner:
    """Filtra y rankea instrumentos por volatilidad, volumen y liquidez."""

    def __init__(
        self,
        weights: ScannerWeights | None = None,
        *,
        gap_policy: GapPolicy = GapPolicy.FORWARD_FILL,
    ) -> None:
        self._weights = weights or ScannerWeights()
        self._gap_policy = gap_policy

    def scan(
        self,
        bars_by_instrument: Mapping[str, Sequence[Bar]],
        *,
        top_n: int = 5,
        min_bars: int = 3,
    ) -> ScannerResult:
        raw: list[AssetScore] = []
        gap_events: list[str] = []
        for instrument_id, bars in bars_by_instrument.items():
            aligned, events = align_bars_for_gaps(bars, policy=self._gap_policy)
            gap_events.extend(events)
            if len(aligned) < min_bars:
                continue
            # Excluir sintéticas volume==0 de liquidez Y volatilidad (TD-11)
            live = [b for b in aligned if b.volume > 0]
            base = live or list(aligned)
            closes = [float(b.close) for b in base]
            volumes = [float(b.volume) for b in base]
            ranges = [float((b.high - b.low) / b.close) if b.close > 0 else 0.0 for b in base]
            rets = [
                (closes[i] - closes[i - 1]) / closes[i - 1]
                for i in range(1, len(closes))
                if closes[i - 1] != 0
            ]
            vol = pstdev(rets) if len(rets) > 1 else 0.0
            vol_score = float(vol)
            volume_score = mean(volumes) if volumes else 0.0
            avg_range = mean(ranges) if ranges else 1.0
            liquidity_score = 1.0 / (avg_range + 1e-9)
            raw.append(
                AssetScore(
                    instrument_id=instrument_id,
                    volatility=vol_score,
                    volume_score=volume_score,
                    liquidity_score=liquidity_score,
                    composite=0.0,
                )
            )

        if not raw:
            return ScannerResult(scores=(), selected=(), gap_events=tuple(gap_events))

        def norm(values: list[float]) -> list[float]:
            lo, hi = min(values), max(values)
            if hi <= lo:
                return [0.0 for _ in values]
            return [(v - lo) / (hi - lo) for v in values]

        vols = norm([s.volatility for s in raw])
        vols_n = norm([s.volume_score for s in raw])
        liqs = norm([s.liquidity_score for s in raw])
        w = self._weights
        scored: list[AssetScore] = []
        for i, s in enumerate(raw):
            composite = w.volatility * vols[i] + w.volume * vols_n[i] + w.liquidity * liqs[i]
            scored.append(
                AssetScore(
                    instrument_id=s.instrument_id,
                    volatility=s.volatility,
                    volume_score=s.volume_score,
                    liquidity_score=s.liquidity_score,
                    composite=round(composite, 8),
                    volatility_n=vols[i],
                    volume_n=vols_n[i],
                    liquidity_n=liqs[i],
                )
            )
        scored.sort(key=lambda x: (-x.composite, x.instrument_id))
        selected = tuple(s.instrument_id for s in scored[: max(0, top_n)])
        return ScannerResult(
            scores=tuple(scored),
            selected=selected,
            gap_events=tuple(gap_events),
        )
