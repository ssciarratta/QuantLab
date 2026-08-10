"""Perfiles de scoring Alpha Scanner (FASE 5).

Cada perfil declara factores/pesos; el default del lab sigue siendo legacy_v1
via AlphaScanner. Estos perfiles usan CompositeScorer + FeatureCalculator.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from quantlab.core.types.market import Bar
from quantlab.research.alpha.features import FeatureCalculator, MarketExtras
from quantlab.research.alpha.models import MissingFactorPolicy, NormalizationMethod
from quantlab.research.alpha.scoring import (
    CompositeScorer,
    FactorSpec,
    ScoredRow,
    legacy_factor_specs,
)

PROFILE_LEGACY_V1 = "legacy_v1"
PROFILE_MOMENTUM = "momentum"
PROFILE_MEAN_REVERSION = "mean_reversion"
PROFILE_MARKET_MAKING = "market_making"
PROFILE_AVELLANEDA_STOIKOV = "avellaneda_stoikov"
PROFILE_FUNDING = "funding"
PROFILE_BALANCED = "balanced"
PROFILE_TREND = "trend"
PROFILE_OPTIONS = "options"

PROFILE_VERSION = "profiles-v1"

# Ramas del Simulador (sin Demo) — selector Alpha Scanner.
SCANNER_FAMILY_ORDER: tuple[str, ...] = (
    "trend",
    "momentum",
    "mean_reversion",
    "market_making",
    "stats",
    "ml",
    "multi_asset",
    "microstructure",
    "arbitrage",
    "options",
)

# Familia UI → perfil de scoring interno (factores).
FAMILY_SCORING_ALIAS: dict[str, str] = {
    "trend": PROFILE_TREND,
    "momentum": PROFILE_MOMENTUM,
    "mean_reversion": PROFILE_MEAN_REVERSION,
    "market_making": PROFILE_MARKET_MAKING,
    "stats": PROFILE_FUNDING,
    "ml": PROFILE_BALANCED,
    "multi_asset": PROFILE_BALANCED,
    "microstructure": PROFILE_MARKET_MAKING,
    "arbitrage": PROFILE_FUNDING,
    "options": PROFILE_OPTIONS,
}

# Labels cortos ES para selector Guided Lab / GET profiles (técnicos).
PROFILE_LABELS_ES: dict[str, str] = {
    PROFILE_LEGACY_V1: "legacy_v1 (default lab)",
    PROFILE_MOMENTUM: "momentum (tendencia)",
    PROFILE_MEAN_REVERSION: "mean_reversion (media-reversión)",
    PROFILE_MARKET_MAKING: "market_making (MM)",
    PROFILE_AVELLANEDA_STOIKOV: "avellaneda_stoikov (AS)",
    PROFILE_FUNDING: "funding (funding/OI)",
    PROFILE_BALANCED: "balanced (equilibrado)",
    PROFILE_TREND: "trend (tendencial)",
    PROFILE_OPTIONS: "options (vol)",
}


@dataclass(frozen=True, slots=True)
class ScoringProfile:
    name: str
    version: str
    description: str
    factors: tuple[FactorSpec, ...]
    normalization: NormalizationMethod = NormalizationMethod.MIN_MAX_CROSS_SECTIONAL
    missing_policy: MissingFactorPolicy = MissingFactorPolicy.RENORMALIZE_AVAILABLE
    apply_quality_penalties: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "label_es": PROFILE_LABELS_ES.get(self.name, self.name),
            "factors": [
                {
                    "name": f.name,
                    "weight": f.weight,
                    "higher_is_better": f.higher_is_better,
                }
                for f in self.factors
            ],
            "normalization": self.normalization.value,
            "missing_policy": self.missing_policy.value,
            "apply_quality_penalties": self.apply_quality_penalties,
        }


def _f(
    name: str,
    weight: float,
    *,
    higher_is_better: bool = True,
) -> FactorSpec:
    getters = {
        "volatility": lambda fv: fv.volatility,
        "volume": lambda fv: fv.volume_score,
        "liquidity": lambda fv: fv.liquidity_score,
        "momentum": lambda fv: fv.momentum,
        "trend_quality": lambda fv: fv.trend_quality,
        "spread": lambda fv: fv.spread,
        "depth": lambda fv: fv.depth,
        "volume_quality": lambda fv: fv.volume_quality,
        "volatility_quality": lambda fv: fv.volatility_quality,
        "funding": lambda fv: fv.funding,
        "open_interest": lambda fv: fv.open_interest,
        "persistence": lambda fv: fv.persistence,
    }
    return FactorSpec(
        name=name,
        weight=weight,
        higher_is_better=higher_is_better,
        getter=getters[name],
    )


def build_profile(name: str) -> ScoringProfile:
    key = name.strip().lower()
    # Alias familia Simulador → scoring interno (p.ej. ml → balanced).
    if key in FAMILY_SCORING_ALIAS and FAMILY_SCORING_ALIAS[key] != key:
        key = FAMILY_SCORING_ALIAS[key]
    if key in (PROFILE_LEGACY_V1, "legacy"):
        return ScoringProfile(
            name=PROFILE_LEGACY_V1,
            version=PROFILE_VERSION,
            description="Volatilidad + volumen + liquidez OHLC (fórmula F4/F111).",
            factors=legacy_factor_specs(),
            missing_policy=MissingFactorPolicy.RENORMALIZE_AVAILABLE,
        )
    if key == PROFILE_TREND:
        return ScoringProfile(
            name=PROFILE_TREND,
            version=PROFILE_VERSION,
            description="Tendenciales: calidad de tendencia + momentum + vol relativa.",
            factors=(
                _f("trend_quality", 0.40),
                _f("momentum", 0.25),
                _f("volatility", 0.20),
                _f("volume", 0.15),
            ),
        )
    if key == PROFILE_MOMENTUM:
        return ScoringProfile(
            name=PROFILE_MOMENTUM,
            version=PROFILE_VERSION,
            description="Prioriza momentum, tendencia y volatilidad relativa.",
            factors=(
                _f("momentum", 0.40),
                _f("trend_quality", 0.25),
                _f("volatility", 0.20),
                _f("volume", 0.15),
            ),
        )
    if key in (PROFILE_MEAN_REVERSION, "mr", "mean-reversion"):
        return ScoringProfile(
            name=PROFILE_MEAN_REVERSION,
            version=PROFILE_VERSION,
            description="Favorece media-reversión: anti-momentum + liquidez + baja persistencia.",
            factors=(
                _f("momentum", 0.35, higher_is_better=False),
                _f("liquidity", 0.30),
                _f("persistence", 0.20, higher_is_better=False),
                _f("spread", 0.15, higher_is_better=False),
            ),
            missing_policy=MissingFactorPolicy.RENORMALIZE_AVAILABLE,
        )
    if key in (PROFILE_MARKET_MAKING, "mm", "market-making"):
        return ScoringProfile(
            name=PROFILE_MARKET_MAKING,
            version=PROFILE_VERSION,
            description="MM: liquidez, spread estrecho, volumen estable.",
            factors=(
                _f("liquidity", 0.30),
                _f("spread", 0.30, higher_is_better=False),
                _f("volume_quality", 0.20),
                _f("volume", 0.20),
            ),
        )
    if key in (PROFILE_AVELLANEDA_STOIKOV, "as", "avellaneda-stoikov"):
        return ScoringProfile(
            name=PROFILE_AVELLANEDA_STOIKOV,
            version=PROFILE_VERSION,
            description="AS: spread/volatilidad/volumen (inventario implícito vía vol).",
            factors=(
                _f("spread", 0.30, higher_is_better=False),
                _f("volatility", 0.30),
                _f("liquidity", 0.25),
                _f("volume", 0.15),
            ),
        )
    if key == PROFILE_FUNDING:
        return ScoringProfile(
            name=PROFILE_FUNDING,
            version=PROFILE_VERSION,
            description="Funding/OI cuando hay datos; si faltan, renormaliza (no finge 0).",
            factors=(
                _f("funding", 0.35, higher_is_better=False),
                _f("open_interest", 0.25),
                _f("volume", 0.20),
                _f("liquidity", 0.20),
            ),
            missing_policy=MissingFactorPolicy.RENORMALIZE_AVAILABLE,
        )
    if key == PROFILE_BALANCED:
        return ScoringProfile(
            name=PROFILE_BALANCED,
            version=PROFILE_VERSION,
            description="Mezcla equilibrada momentum + liquidez + calidad.",
            factors=(
                _f("momentum", 0.20),
                _f("liquidity", 0.20),
                _f("volume", 0.15),
                _f("volatility", 0.15),
                _f("trend_quality", 0.15),
                _f("volume_quality", 0.15),
            ),
            normalization=NormalizationMethod.ROBUST_CROSS_SECTIONAL,
            apply_quality_penalties=True,
        )
    if key == PROFILE_OPTIONS:
        return ScoringProfile(
            name=PROFILE_OPTIONS,
            version=PROFILE_VERSION,
            description="Opciones/vol: volatilidad + liquidez + volumen (proxy OHLC).",
            factors=(
                _f("volatility", 0.40),
                _f("liquidity", 0.25),
                _f("volume", 0.20),
                _f("momentum", 0.15),
            ),
        )
    raise ValueError(f"perfil desconocido: {name!r}")


def list_profiles() -> tuple[str, ...]:
    """Perfiles técnicos de scoring (compat FASE 5 + trend/options)."""
    return (
        PROFILE_LEGACY_V1,
        PROFILE_TREND,
        PROFILE_MOMENTUM,
        PROFILE_MEAN_REVERSION,
        PROFILE_MARKET_MAKING,
        PROFILE_AVELLANEDA_STOIKOV,
        PROFILE_FUNDING,
        PROFILE_BALANCED,
        PROFILE_OPTIONS,
    )


def score_with_profile(
    bars_by_instrument: Mapping[str, Sequence[Bar]],
    profile: str | ScoringProfile,
    *,
    extras_by_instrument: Mapping[str, MarketExtras] | None = None,
    top_n: int | None = None,
) -> tuple[ScoredRow, ...]:
    """FeatureCalculator → CompositeScorer bajo un perfil nombrado."""
    prof = profile if isinstance(profile, ScoringProfile) else build_profile(profile)
    feats = FeatureCalculator().compute_many(
        bars_by_instrument,
        extras_by_instrument=extras_by_instrument,
    )
    scorer = CompositeScorer(
        factors=prof.factors,
        normalization=prof.normalization,
        missing_policy=prof.missing_policy,
        apply_quality_penalties=prof.apply_quality_penalties,
    )
    rows = scorer.score(feats, top_n=top_n)
    return rows


def profile_catalog() -> list[dict[str, Any]]:
    """Catálogo técnico (compat Guided Lab / tests FASE 5)."""
    return [build_profile(n).to_dict() for n in list_profiles()]


def scanner_family_catalog() -> list[dict[str, Any]]:
    """Catálogo UI Alpha Scanner = familias del Simulador (sin Demo)."""
    from quantlab.workbench.strategy_guides import FAMILY_LABELS_ES

    out: list[dict[str, Any]] = []
    for fam in SCANNER_FAMILY_ORDER:
        scoring_key = FAMILY_SCORING_ALIAS.get(fam, fam)
        try:
            scoring = build_profile(scoring_key)
        except ValueError:
            scoring = build_profile(PROFILE_BALANCED)
        label = FAMILY_LABELS_ES.get(fam, fam)
        out.append(
            {
                "name": fam,
                "family": fam,
                "version": PROFILE_VERSION,
                "label_es": label,
                "description": (
                    f"Rama «{label}»: rankea monedas para estrategias de esa familia. "
                    f"Scoring interno: {scoring.name}."
                ),
                "scoring_profile": scoring.name,
                "factors": [
                    {
                        "name": f.name,
                        "weight": f.weight,
                        "higher_is_better": f.higher_is_better,
                    }
                    for f in scoring.factors
                ],
                "normalization": scoring.normalization.value,
                "missing_policy": scoring.missing_policy.value,
                "apply_quality_penalties": scoring.apply_quality_penalties,
            }
        )
    return out


__all__ = [
    "FAMILY_SCORING_ALIAS",
    "PROFILE_AVELLANEDA_STOIKOV",
    "PROFILE_BALANCED",
    "PROFILE_FUNDING",
    "PROFILE_LABELS_ES",
    "PROFILE_LEGACY_V1",
    "PROFILE_MARKET_MAKING",
    "PROFILE_MEAN_REVERSION",
    "PROFILE_MOMENTUM",
    "PROFILE_OPTIONS",
    "PROFILE_TREND",
    "PROFILE_VERSION",
    "SCANNER_FAMILY_ORDER",
    "ScoringProfile",
    "build_profile",
    "list_profiles",
    "profile_catalog",
    "scanner_family_catalog",
    "score_with_profile",
]
