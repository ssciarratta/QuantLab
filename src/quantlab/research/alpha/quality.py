"""Calidad de datos e elegibilidad para Alpha Scanner (FASE 2)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from statistics import mean
from typing import Any

from quantlab.core.types.market import Bar
from quantlab.research.alpha import GapPolicy, align_bars_for_gaps


class ExclusionReason(StrEnum):
    INSUFFICIENT_HISTORY = "insufficient_history"
    INSUFFICIENT_VOLUME = "insufficient_volume"
    EXCESSIVE_SPREAD = "excessive_spread"
    STALE_DATA = "stale_data"
    LOW_DATA_COMPLETENESS = "low_data_completeness"
    NEW_MARKET = "new_market"
    INVALID_PRICE = "invalid_price"
    MISSING_BARS = "missing_bars"
    FETCH_FAILED = "fetch_failed"
    UNSUPPORTED_MARKET_TYPE = "unsupported_market_type"


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    instrument_id: str
    expected_bars: int
    valid_bars: int
    completeness: float
    gaps: int
    duplicates: int
    invalid_values: int
    out_of_order_records: int
    latest_market_timestamp: datetime | None
    fetch_timestamp: datetime
    freshness_ms: float | None
    is_stale: bool
    candles_available: bool
    quality_score: float
    # Ausencia explícita (nunca fingir 0 como “disponible”)
    ticker_available: bool | None = None
    trades_available: bool | None = None
    order_book_available: bool | None = None
    funding_available: bool | None = None
    open_interest_available: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "expected_bars": self.expected_bars,
            "valid_bars": self.valid_bars,
            "completeness": self.completeness,
            "gaps": self.gaps,
            "duplicates": self.duplicates,
            "invalid_values": self.invalid_values,
            "out_of_order_records": self.out_of_order_records,
            "latest_market_timestamp": (
                self.latest_market_timestamp.isoformat()
                if self.latest_market_timestamp
                else None
            ),
            "fetch_timestamp": self.fetch_timestamp.isoformat(),
            "freshness_ms": self.freshness_ms,
            "is_stale": self.is_stale,
            "candles_available": self.candles_available,
            "quality_score": self.quality_score,
            "ticker_available": self.ticker_available,
            "trades_available": self.trades_available,
            "order_book_available": self.order_book_available,
            "funding_available": self.funding_available,
            "open_interest_available": self.open_interest_available,
        }


@dataclass(frozen=True, slots=True)
class EligibilityResult:
    instrument_id: str
    eligible: bool
    reasons: tuple[ExclusionReason, ...]
    detail: str = ""
    quality: DataQualityReport | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "eligible": self.eligible,
            "reasons": [r.value for r in self.reasons],
            "detail": self.detail,
            "quality": self.quality.to_dict() if self.quality else None,
        }


@dataclass(frozen=True, slots=True)
class EligibilityConfig:
    min_bars: int = 3
    min_mean_volume: float | None = None
    min_completeness: float = 0.80
    max_freshness_ms: float | None = None
    max_gap_ratio: float = 0.50
    stale_if_no_timestamp: bool = False


def assess_bar_quality(
    instrument_id: str,
    bars: Sequence[Bar],
    *,
    expected_bars: int | None = None,
    fetch_timestamp: datetime | None = None,
    max_freshness_ms: float | None = None,
    gap_policy: GapPolicy = GapPolicy.FORWARD_FILL,
) -> DataQualityReport:
    """Evalúa calidad OHLCV. Campos no disponibles → None (no 0 fingido)."""
    now = fetch_timestamp or datetime.now(tz=UTC)
    expected = expected_bars if expected_bars is not None else len(bars)

    invalid = 0
    duplicates = 0
    out_of_order = 0
    seen_ts: set[datetime] = set()
    prev_close: datetime | None = None
    valid = 0

    for bar in bars:
        bad = False
        for px in (bar.open, bar.high, bar.low, bar.close):
            if px is None or px <= 0:
                bad = True
                break
        if bar.volume is None or bar.volume < 0:
            bad = True
        if bad:
            invalid += 1
            continue
        valid += 1
        ts = bar.timestamp_close
        if ts in seen_ts:
            duplicates += 1
        seen_ts.add(ts)
        if prev_close is not None and ts < prev_close:
            out_of_order += 1
        prev_close = ts

    aligned, gap_events = align_bars_for_gaps(bars, policy=gap_policy)
    # gaps ≈ fills sintéticos (volume==0) insertados
    gaps = sum(1 for b in aligned if b.volume == 0) if gap_events else len(gap_events)

    completeness = (valid / expected) if expected > 0 else 0.0
    latest = bars[-1].timestamp_close if bars else None
    freshness_ms = (
        max(0.0, (now - latest).total_seconds() * 1000.0) if latest is not None else None
    )

    is_stale = bool(
        max_freshness_ms is not None
        and (freshness_ms is None or freshness_ms > max_freshness_ms)
    )

    # quality_score: combinar completeness y penalizar defectos (0–1)
    defect_pen = min(
        1.0,
        (invalid + duplicates + out_of_order) / max(1, expected) + (gaps / max(1, expected)) * 0.5,
    )
    quality_score = max(0.0, min(1.0, completeness * (1.0 - 0.5 * defect_pen)))
    if is_stale:
        quality_score = min(quality_score, 0.4)

    return DataQualityReport(
        instrument_id=instrument_id,
        expected_bars=expected,
        valid_bars=valid,
        completeness=round(completeness, 6),
        gaps=gaps,
        duplicates=duplicates,
        invalid_values=invalid,
        out_of_order_records=out_of_order,
        latest_market_timestamp=latest,
        fetch_timestamp=now,
        freshness_ms=freshness_ms,
        is_stale=is_stale,
        candles_available=len(bars) > 0,
        quality_score=round(quality_score, 6),
        ticker_available=None,
        trades_available=None,
        order_book_available=None,
        funding_available=None,
        open_interest_available=None,
    )


def evaluate_eligibility(
    instrument_id: str,
    bars: Sequence[Bar] | None,
    *,
    config: EligibilityConfig | None = None,
    fetch_failed: bool = False,
    fetch_error: str = "",
) -> EligibilityResult:
    """Decide elegibilidad con motivos tipados (nunca silencio)."""
    cfg = config or EligibilityConfig()
    reasons: list[ExclusionReason] = []
    detail_parts: list[str] = []

    if fetch_failed or bars is None:
        reasons.append(ExclusionReason.FETCH_FAILED)
        detail_parts.append(fetch_error or "sin barras")
        return EligibilityResult(
            instrument_id=instrument_id,
            eligible=False,
            reasons=tuple(reasons),
            detail="; ".join(detail_parts),
            quality=None,
        )

    quality = assess_bar_quality(
        instrument_id,
        bars,
        expected_bars=max(cfg.min_bars, len(bars)),
        max_freshness_ms=cfg.max_freshness_ms,
    )

    if quality.valid_bars < cfg.min_bars:
        reasons.append(ExclusionReason.INSUFFICIENT_HISTORY)
        detail_parts.append(f"valid_bars={quality.valid_bars}<{cfg.min_bars}")

    if quality.completeness < cfg.min_completeness:
        reasons.append(ExclusionReason.LOW_DATA_COMPLETENESS)
        detail_parts.append(f"completeness={quality.completeness}")

    if quality.is_stale:
        reasons.append(ExclusionReason.STALE_DATA)
        detail_parts.append(f"freshness_ms={quality.freshness_ms}")

    if quality.invalid_values > 0:
        reasons.append(ExclusionReason.INVALID_PRICE)
        detail_parts.append(f"invalid_values={quality.invalid_values}")

    if cfg.min_mean_volume is not None and bars:
        live_vols = [float(b.volume) for b in bars if b.volume > 0]
        mean_vol = mean(live_vols) if live_vols else None
        if mean_vol is None:
            reasons.append(ExclusionReason.INSUFFICIENT_VOLUME)
            detail_parts.append("mean_volume=unavailable")
        elif mean_vol < cfg.min_mean_volume:
            reasons.append(ExclusionReason.INSUFFICIENT_VOLUME)
            detail_parts.append(f"mean_volume={mean_vol}")

    expected = max(1, quality.expected_bars)
    if quality.gaps / expected > cfg.max_gap_ratio:
        reasons.append(ExclusionReason.LOW_DATA_COMPLETENESS)
        detail_parts.append(f"gap_ratio={quality.gaps / expected:.3f}")

    eligible = len(reasons) == 0
    return EligibilityResult(
        instrument_id=instrument_id,
        eligible=eligible,
        reasons=tuple(reasons),
        detail="; ".join(detail_parts),
        quality=quality,
    )
