"""Normalizacion, penalties y CompositeScorer (FASE 4).

El path default del lab sigue siendo AlphaScanner / legacy_v1.
Este modulo habilita scoring versionado sobre FeatureVector sin romper el baseline.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from statistics import median
from typing import Any

from quantlab.research.alpha.features import FeatureVector
from quantlab.research.alpha.models import (
    FeatureComponent,
    MissingFactorPolicy,
    NormalizationMethod,
)

FORMULA_VERSION_COMPOSITE_V1 = "composite-scorer-v1"
SCORER_VERSION = "alpha-scorer-v1"


@dataclass(frozen=True, slots=True)
class FactorSpec:
    name: str
    weight: float
    higher_is_better: bool = True
    getter: Callable[[FeatureVector], float | None] | None = None


@dataclass(frozen=True, slots=True)
class Penalty:
    name: str
    value: float
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ScoredRow:
    instrument_id: str
    composite: float
    base_score: float
    components: tuple[FeatureComponent, ...]
    penalties: tuple[Penalty, ...]
    excluded: bool = False
    exclusion_reason: str = ""
    formula_version: str = FORMULA_VERSION_COMPOSITE_V1
    normalization_method: str = NormalizationMethod.MIN_MAX_CROSS_SECTIONAL.value
    missing_factor_policy: str = MissingFactorPolicy.RENORMALIZE_AVAILABLE.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
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
            "penalties": [
                {"name": p.name, "value": p.value, "detail": p.detail} for p in self.penalties
            ],
            "excluded": self.excluded,
            "exclusion_reason": self.exclusion_reason,
            "formula_version": self.formula_version,
            "normalization_method": self.normalization_method,
            "missing_factor_policy": self.missing_factor_policy,
        }


def legacy_factor_specs(
    *,
    volatility: float = 0.35,
    volume: float = 0.35,
    liquidity: float = 0.30,
) -> tuple[FactorSpec, ...]:
    return (
        FactorSpec("volatility", volatility, getter=lambda fv: fv.volatility),
        FactorSpec("volume", volume, getter=lambda fv: fv.volume_score),
        FactorSpec("liquidity", liquidity, getter=lambda fv: fv.liquidity_score),
    )


def _get_raw(fv: FeatureVector, spec: FactorSpec) -> float | None:
    if spec.getter is not None:
        return spec.getter(fv)
    return getattr(fv, spec.name, None)


def min_max_normalize(values: Sequence[float | None]) -> list[float | None]:
    present = [v for v in values if v is not None]
    if not present:
        return [None for _ in values]
    lo, hi = min(present), max(present)
    if hi <= lo:
        # 1 valor (o empate total): sin cross-section útil.
        # Con N=1 devolver 0.5 (neutro); con N≥2 empatados seguir en 0 (degradado).
        fill = 0.5 if len(present) == 1 else 0.0
        return [fill if v is not None else None for v in values]
    out: list[float | None] = []
    for v in values:
        if v is None:
            out.append(None)
        else:
            out.append((v - lo) / (hi - lo))
    return out


def _iqr(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 0:
        lower = ordered[:mid]
        upper = ordered[mid:]
    else:
        lower = ordered[:mid]
        upper = ordered[mid + 1 :]
    if not lower or not upper:
        return 0.0
    q1 = float(median(lower))
    q3 = float(median(upper))
    return max(0.0, q3 - q1)


def robust_normalize(values: Sequence[float | None]) -> list[float | None]:
    """(x - median) / IQR then min-max to [0,1]."""
    present = [v for v in values if v is not None]
    if not present:
        return [None for _ in values]
    med = float(median(present))
    iqr = _iqr(present)
    scale = iqr if iqr > 1e-12 else 1.0
    robust: list[float | None] = []
    for v in values:
        if v is None:
            robust.append(None)
        else:
            robust.append((v - med) / scale)
    return min_max_normalize(robust)


def normalize_column(
    values: Sequence[float | None],
    method: NormalizationMethod,
) -> list[float | None]:
    if method is NormalizationMethod.ROBUST_CROSS_SECTIONAL:
        return robust_normalize(values)
    return min_max_normalize(values)


class PenaltyEngine:
    """Penalizaciones explicitas (restan del composite)."""

    def __init__(
        self,
        *,
        missing_factor_penalty: float = 0.05,
        low_volume_quality_threshold: float = 0.5,
        low_volume_quality_penalty: float = 0.03,
        low_volatility_quality_threshold: float = 0.2,
        low_volatility_quality_penalty: float = 0.02,
    ) -> None:
        self.missing_factor_penalty = missing_factor_penalty
        self.low_volume_quality_threshold = low_volume_quality_threshold
        self.low_volume_quality_penalty = low_volume_quality_penalty
        self.low_volatility_quality_threshold = low_volatility_quality_threshold
        self.low_volatility_quality_penalty = low_volatility_quality_penalty

    def evaluate(
        self,
        fv: FeatureVector,
        *,
        missing_factor_names: Sequence[str] = (),
        apply_missing_penalty: bool = False,
    ) -> tuple[Penalty, ...]:
        pens: list[Penalty] = []
        if apply_missing_penalty and missing_factor_names:
            pens.append(
                Penalty(
                    name="missing_factors",
                    value=self.missing_factor_penalty * len(missing_factor_names),
                    detail=",".join(missing_factor_names),
                )
            )
        if fv.volume_quality is not None and fv.volume_quality < self.low_volume_quality_threshold:
            pens.append(
                Penalty(
                    name="low_volume_quality",
                    value=self.low_volume_quality_penalty,
                    detail=f"volume_quality={fv.volume_quality}",
                )
            )
        if (
            fv.volatility_quality is not None
            and fv.volatility_quality < self.low_volatility_quality_threshold
        ):
            pens.append(
                Penalty(
                    name="low_volatility_quality",
                    value=self.low_volatility_quality_penalty,
                    detail=f"volatility_quality={fv.volatility_quality}",
                )
            )
        return tuple(pens)


class CompositeScorer:
    """Scorea FeatureVectors con normalizacion, missing policies y penalties."""

    def __init__(
        self,
        factors: Sequence[FactorSpec] | None = None,
        *,
        normalization: NormalizationMethod = NormalizationMethod.MIN_MAX_CROSS_SECTIONAL,
        missing_policy: MissingFactorPolicy = MissingFactorPolicy.RENORMALIZE_AVAILABLE,
        penalty_engine: PenaltyEngine | None = None,
        apply_quality_penalties: bool = False,
        profile_fallback: float = 0.5,
        formula_version: str = FORMULA_VERSION_COMPOSITE_V1,
    ) -> None:
        self.factors = tuple(factors or legacy_factor_specs())
        self.normalization = normalization
        self.missing_policy = missing_policy
        self.penalty_engine = penalty_engine or PenaltyEngine()
        self.apply_quality_penalties = apply_quality_penalties
        self.profile_fallback = profile_fallback
        self.formula_version = formula_version

    def score(
        self,
        vectors: Mapping[str, FeatureVector] | Sequence[FeatureVector],
        *,
        top_n: int | None = None,
    ) -> tuple[ScoredRow, ...]:
        del top_n
        items: list[FeatureVector] = (
            list(vectors.values()) if isinstance(vectors, Mapping) else list(vectors)
        )
        if not items:
            return ()

        raw_cols: dict[str, list[float | None]] = {}
        for spec in self.factors:
            raw_cols[spec.name] = [_get_raw(fv, spec) for fv in items]

        for spec in self.factors:
            if not spec.higher_is_better:
                col = raw_cols[spec.name]
                present = [v for v in col if v is not None]
                if present:
                    mx = max(present)
                    raw_cols[spec.name] = [None if v is None else (mx - v) for v in col]

        norm_cols: dict[str, list[float | None]] = {
            name: normalize_column(vals, self.normalization) for name, vals in raw_cols.items()
        }

        rows = [self._score_one(fv, i, raw_cols, norm_cols) for i, fv in enumerate(items)]
        ranked = sorted(
            [r for r in rows if not r.excluded],
            key=lambda r: (-r.composite, r.instrument_id),
        )
        excluded = sorted(
            [r for r in rows if r.excluded],
            key=lambda r: r.instrument_id,
        )
        return tuple(ranked + excluded)

    def _score_one(
        self,
        fv: FeatureVector,
        idx: int,
        raw_cols: Mapping[str, Sequence[float | None]],
        norm_cols: Mapping[str, Sequence[float | None]],
    ) -> ScoredRow:
        avail: list[tuple[FactorSpec, float | None, float | None]] = []
        missing_names: list[str] = []
        for spec in self.factors:
            raw = raw_cols[spec.name][idx]
            norm = norm_cols[spec.name][idx]
            if raw is None or norm is None:
                missing_names.append(spec.name)
            avail.append((spec, raw, norm))

        if missing_names and self.missing_policy is MissingFactorPolicy.EXCLUDE_CANDIDATE:
            return ScoredRow(
                instrument_id=fv.instrument_id,
                composite=0.0,
                base_score=0.0,
                components=(),
                penalties=(),
                excluded=True,
                exclusion_reason=f"missing_factors:{','.join(missing_names)}",
                formula_version=self.formula_version,
                normalization_method=self.normalization.value,
                missing_factor_policy=self.missing_policy.value,
            )

        components: list[FeatureComponent] = []
        weighted = 0.0

        if self.missing_policy is MissingFactorPolicy.RENORMALIZE_AVAILABLE:
            present_w = sum(s.weight for s, r, n in avail if r is not None and n is not None)
            for spec, raw, norm in avail:
                if raw is None or norm is None:
                    components.append(
                        FeatureComponent(
                            name=spec.name,
                            raw=None,
                            normalized=None,
                            weight=0.0,
                            contribution=None,
                            available=False,
                        )
                    )
                    continue
                w_eff = (spec.weight / present_w) if present_w > 0 else 0.0
                contrib = w_eff * norm
                weighted += contrib
                components.append(
                    FeatureComponent(
                        name=spec.name,
                        raw=float(raw),
                        normalized=float(norm),
                        weight=float(w_eff),
                        contribution=round(contrib, 8),
                        available=True,
                    )
                )
        else:
            for spec, raw, norm in avail:
                if raw is None or norm is None:
                    if self.missing_policy is MissingFactorPolicy.USE_PROFILE_FALLBACK:
                        fill = self.profile_fallback
                        contrib = spec.weight * fill
                        weighted += contrib
                        components.append(
                            FeatureComponent(
                                name=spec.name,
                                raw=None,
                                normalized=fill,
                                weight=float(spec.weight),
                                contribution=round(contrib, 8),
                                available=False,
                            )
                        )
                    else:
                        components.append(
                            FeatureComponent(
                                name=spec.name,
                                raw=None,
                                normalized=0.0,
                                weight=float(spec.weight),
                                contribution=0.0,
                                available=False,
                            )
                        )
                    continue
                contrib = spec.weight * norm
                weighted += contrib
                components.append(
                    FeatureComponent(
                        name=spec.name,
                        raw=float(raw),
                        normalized=float(norm),
                        weight=float(spec.weight),
                        contribution=round(contrib, 8),
                        available=True,
                    )
                )

        base = round(weighted, 8)
        apply_missing_pen = self.missing_policy is MissingFactorPolicy.PENALIZE_MISSING
        pens = self.penalty_engine.evaluate(
            fv,
            missing_factor_names=missing_names,
            apply_missing_penalty=apply_missing_pen,
        )
        if not self.apply_quality_penalties:
            pens = tuple(p for p in pens if p.name == "missing_factors")
        pen_sum = sum(p.value for p in pens)
        composite = round(max(0.0, base - pen_sum), 8)
        return ScoredRow(
            instrument_id=fv.instrument_id,
            composite=composite,
            base_score=base,
            components=tuple(components),
            penalties=pens,
            formula_version=self.formula_version,
            normalization_method=self.normalization.value,
            missing_factor_policy=self.missing_policy.value,
        )


__all__ = [
    "FORMULA_VERSION_COMPOSITE_V1",
    "SCORER_VERSION",
    "CompositeScorer",
    "FactorSpec",
    "Penalty",
    "PenaltyEngine",
    "ScoredRow",
    "legacy_factor_specs",
    "min_max_normalize",
    "normalize_column",
    "robust_normalize",
]
