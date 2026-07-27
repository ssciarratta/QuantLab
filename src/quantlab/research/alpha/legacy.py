"""Adapter legacy_v1: ejecuta AlphaScanner actual y mapea a AlphaScanResult."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from uuid import uuid4

from quantlab.core.types.market import Bar
from quantlab.research.alpha import AlphaScanner, AssetScore, ScannerResult, ScannerWeights
from quantlab.research.alpha.explain import explain_scores
from quantlab.research.alpha.models import (
    FORMULA_VERSION_LEGACY,
    PROFILE_LEGACY_V1,
    PROFILE_VERSION_LEGACY,
    SCANNER_VERSION,
    AlphaScanRequest,
    AlphaScanResult,
    AlphaScanWeights,
    ExclusionRecord,
    FeatureComponent,
    RankedCandidate,
)


def _symbol_from_instrument_id(instrument_id: str) -> str:
    if ":" in instrument_id:
        return instrument_id.split(":", 1)[1]
    return instrument_id


def _venue_from_instrument_id(instrument_id: str, default: str) -> str:
    if instrument_id.startswith("BN:"):
        return "binance"
    if instrument_id.startswith("WB:"):
        return "lab"
    return default


def _components_for(score: AssetScore, weights: ScannerWeights) -> tuple[FeatureComponent, ...]:
    parts = (
        ("volatility", score.volatility, score.volatility_n, weights.volatility),
        ("volume", score.volume_score, score.volume_n, weights.volume),
        ("liquidity", score.liquidity_score, score.liquidity_n, weights.liquidity),
    )
    out: list[FeatureComponent] = []
    for name, raw, norm, w in parts:
        out.append(
            FeatureComponent(
                name=name,
                raw=float(raw),
                normalized=float(norm),
                weight=float(w),
                contribution=round(float(w) * float(norm), 8),
                available=True,
            )
        )
    return tuple(out)


def _strengths(score: AssetScore) -> tuple[str, ...]:
    items: list[str] = []
    if score.volatility_n >= 0.66:
        items.append("Alta volatilidad relativa en el universo")
    if score.volume_n >= 0.66:
        items.append("Volumen relativo alto")
    if score.liquidity_n >= 0.66:
        items.append("Liquidez proxy (rango OHLC) favorable")
    if not items:
        items.append("Sin fortaleza dominante vs el resto del universo")
    return tuple(items)


def _limitations() -> tuple[str, ...]:
    return (
        "Profile legacy_v1: solo vol/volumen/liquidez OHLC",
        "Normalización min-max cross-sectional (sensible a outliers)",
        "Score ≠ rentabilidad garantizada",
    )


def _summary(score: AssetScore, rank: int) -> str:
    return (
        f"Rank #{rank} composite={score.composite:.6g} "
        f"(legacy_v1: vol_n={score.volatility_n:.3g}, "
        f"volume_n={score.volume_n:.3g}, liq_n={score.liquidity_n:.3g}). "
        "Adecuación al perfil, no promesa de PnL."
    )


def map_legacy_result(
    legacy: ScannerResult,
    *,
    request: AlphaScanRequest,
    weights: ScannerWeights,
    fetched: int | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    scan_id: str | None = None,
    exclusions: Sequence[ExclusionRecord] = (),
    warnings: Sequence[str] = (),
) -> AlphaScanResult:
    """Mapea ``ScannerResult`` → ``AlphaScanResult`` sin alterar scores."""
    started = started_at or datetime.now(tz=UTC)
    completed = completed_at or datetime.now(tz=UTC)
    duration_ms = max(0.0, (completed - started).total_seconds() * 1000.0)
    n_fetched = fetched if fetched is not None else len(legacy.scores) + len(exclusions)

    candidates: list[RankedCandidate] = []
    for i, score in enumerate(legacy.scores):
        rank = i + 1
        venue = _venue_from_instrument_id(score.instrument_id, request.venue)
        sym = _symbol_from_instrument_id(score.instrument_id)
        candidates.append(
            RankedCandidate(
                rank=rank,
                venue=venue,
                network=request.network,
                symbol=sym,
                normalized_instrument=score.instrument_id,
                market_type=request.market_type,
                eligible=True,
                composite=float(score.composite),
                base_score=float(score.composite),
                components=_components_for(score, weights),
                penalties=(),
                strengths=_strengths(score),
                limitations=_limitations(),
                summary=_summary(score, rank),
                data_quality=None,
            )
        )

    warn = list(warnings)
    if request.profile != PROFILE_LEGACY_V1:
        warn.append(
            f"profile={request.profile!r} solicitado; FASE 1 ejecuta {PROFILE_LEGACY_V1}"
        )
    warn.append(
        "Un score alto indica adecuación al perfil seleccionado, no rentabilidad garantizada."
    )

    return AlphaScanResult(
        scan_id=scan_id or f"scan_{uuid4().hex[:12]}",
        scanner_version=SCANNER_VERSION,
        profile=PROFILE_LEGACY_V1,
        profile_version=PROFILE_VERSION_LEGACY,
        formula_version=FORMULA_VERSION_LEGACY,
        venue=request.venue,
        network=request.network,
        market_type=request.market_type,
        request=request,
        fetched=n_fetched,
        eligible=len(legacy.scores),
        excluded=len(exclusions),
        top_n=request.top_n,
        candidates=tuple(candidates),
        exclusions=tuple(exclusions),
        warnings=tuple(warn),
        legacy_selected=tuple(legacy.selected),
        legacy_schema_version=legacy.schema_version,
        gap_events=tuple(legacy.gap_events),
        started_at=started,
        completed_at=completed,
        duration_ms=duration_ms,
    )


def run_legacy_v1_scan(
    bars_by_instrument: Mapping[str, Sequence[Bar]],
    request: AlphaScanRequest | None = None,
    *,
    exclusions: Sequence[ExclusionRecord] = (),
) -> AlphaScanResult:
    """Ejecuta el AlphaScanner actual bajo contratos v2."""
    req = request or AlphaScanRequest()
    started = datetime.now(tz=UTC)
    weights = ScannerWeights(
        volatility=req.weights.volatility,
        volume=req.weights.volume,
        liquidity=req.weights.liquidity,
    )
    scanner = AlphaScanner(weights=weights)
    legacy = scanner.scan(
        bars_by_instrument,
        top_n=req.top_n,
        min_bars=req.filters.min_bars,
    )
    # Touch explain path (determinista) — asegura contrib_sum alineada.
    _ = explain_scores(legacy, top=min(3, len(legacy.scores)), weights=weights)
    completed = datetime.now(tz=UTC)
    return map_legacy_result(
        legacy,
        request=req,
        weights=weights,
        fetched=len(bars_by_instrument),
        started_at=started,
        completed_at=completed,
        exclusions=exclusions,
    )


def weights_from_request(request: AlphaScanRequest) -> AlphaScanWeights:
    return request.weights
