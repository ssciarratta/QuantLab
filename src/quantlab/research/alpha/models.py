"""Contratos tipados Alpha Scanner v2 (FASE 1) — compatibles con legacy_v1.

No cambian el scoring: envuelven el ``AlphaScanner`` actual.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class MissingFactorPolicy(StrEnum):
    EXCLUDE_CANDIDATE = "exclude_candidate"
    RENORMALIZE_AVAILABLE = "renormalize_available"
    PENALIZE_MISSING = "penalize_missing"
    USE_PROFILE_FALLBACK = "use_profile_fallback"


class NormalizationMethod(StrEnum):
    MIN_MAX_CROSS_SECTIONAL = "min_max_cross_sectional"  # legacy_v1
    ROBUST_CROSS_SECTIONAL = "robust_cross_sectional"


# Profile que reproduce la fórmula F4/F111 exacta.
PROFILE_LEGACY_V1 = "legacy_v1"
SCANNER_VERSION = "alpha-v2-contracts"
PROFILE_VERSION_LEGACY = "legacy-v1"
FORMULA_VERSION_LEGACY = "composite-minmax-w035-035-030-v1"


@dataclass(frozen=True, slots=True)
class AlphaScanFilters:
    """Filtros de elegibilidad (FASE 1: documentados; enforcement en FASE 2)."""

    min_bars: int = 3
    min_quote_volume: float | None = None
    max_spread_bps: float | None = None
    min_data_completeness: float | None = None
    min_market_age_days: float | None = None


@dataclass(frozen=True, slots=True)
class AlphaScanWeights:
    """Pesos legacy (volatility / volume / liquidity)."""

    volatility: float = 0.35
    volume: float = 0.35
    liquidity: float = 0.30


@dataclass(frozen=True, slots=True)
class AlphaScanRequest:
    """Pedido tipado de scan (FASE 1)."""

    venue: str = "lab"
    network: str = "local"
    market_type: str = "synthetic"
    profile: str = PROFILE_LEGACY_V1
    timeframe: str = "1m"
    lookback_bars: int = 16
    universe_limit: int = 30
    top_n: int = 5
    filters: AlphaScanFilters = field(default_factory=AlphaScanFilters)
    weights: AlphaScanWeights = field(default_factory=AlphaScanWeights)
    missing_factor_policy: MissingFactorPolicy = MissingFactorPolicy.RENORMALIZE_AVAILABLE
    normalization_method: NormalizationMethod = NormalizationMethod.MIN_MAX_CROSS_SECTIONAL
    as_of_time: datetime | None = None
    persist_result: bool = False
    run_backtest: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "network": self.network,
            "market_type": self.market_type,
            "profile": self.profile,
            "timeframe": self.timeframe,
            "lookback_bars": self.lookback_bars,
            "universe_limit": self.universe_limit,
            "top_n": self.top_n,
            "filters": {
                "min_bars": self.filters.min_bars,
                "min_quote_volume": self.filters.min_quote_volume,
                "max_spread_bps": self.filters.max_spread_bps,
                "min_data_completeness": self.filters.min_data_completeness,
                "min_market_age_days": self.filters.min_market_age_days,
            },
            "weights": {
                "volatility": self.weights.volatility,
                "volume": self.weights.volume,
                "liquidity": self.weights.liquidity,
            },
            "missing_factor_policy": self.missing_factor_policy.value,
            "normalization_method": self.normalization_method.value,
            "as_of_time": self.as_of_time.isoformat() if self.as_of_time else None,
            "persist_result": self.persist_result,
            "run_backtest": self.run_backtest,
        }


@dataclass(frozen=True, slots=True)
class FeatureComponent:
    name: str
    raw: float | None
    normalized: float | None
    weight: float
    contribution: float | None
    available: bool = True


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    rank: int
    venue: str
    network: str
    symbol: str
    normalized_instrument: str
    market_type: str
    eligible: bool
    composite: float
    base_score: float
    components: tuple[FeatureComponent, ...]
    penalties: tuple[tuple[str, float], ...] = ()
    strengths: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    summary: str = ""
    data_quality: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "venue": self.venue,
            "network": self.network,
            "symbol": self.symbol,
            "normalized_instrument": self.normalized_instrument,
            "market_type": self.market_type,
            "eligible": self.eligible,
            "composite": self.composite,
            "base_score": self.base_score,
            "components": [
                {
                    "name": c.name,
                    "raw": c.raw,
                    "normalized": c.normalized,
                    "weight": c.weight,
                    "contribution": c.contribution,
                    "available": c.available,
                }
                for c in self.components
            ],
            "penalties": [{"name": n, "value": v} for n, v in self.penalties],
            "strengths": list(self.strengths),
            "limitations": list(self.limitations),
            "summary": self.summary,
            "data_quality": self.data_quality,
        }


@dataclass(frozen=True, slots=True)
class ExclusionRecord:
    symbol: str
    reasons: tuple[str, ...]
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "reasons": list(self.reasons),
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class AlphaScanResult:
    scan_id: str
    scanner_version: str
    profile: str
    profile_version: str
    formula_version: str
    venue: str
    network: str
    market_type: str
    request: AlphaScanRequest
    fetched: int
    eligible: int
    excluded: int
    top_n: int
    candidates: tuple[RankedCandidate, ...]
    exclusions: tuple[ExclusionRecord, ...] = ()
    warnings: tuple[str, ...] = ()
    legacy_selected: tuple[str, ...] = ()
    legacy_schema_version: str = "1.0"
    gap_events: tuple[str, ...] = ()
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    note: str = (
        "Un score alto indica adecuación al perfil seleccionado, "
        "no rentabilidad garantizada."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "scanner_version": self.scanner_version,
            "profile": self.profile,
            "profile_version": self.profile_version,
            "formula_version": self.formula_version,
            "venue": self.venue,
            "network": self.network,
            "market_type": self.market_type,
            "request": self.request.to_dict(),
            "fetched": self.fetched,
            "eligible": self.eligible,
            "excluded": self.excluded,
            "top_n": self.top_n,
            "candidates": [c.to_dict() for c in self.candidates],
            "exclusions": [e.to_dict() for e in self.exclusions],
            "warnings": list(self.warnings),
            "legacy_selected": list(self.legacy_selected),
            "legacy_schema_version": self.legacy_schema_version,
            "gap_events": list(self.gap_events),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "note": self.note,
        }
