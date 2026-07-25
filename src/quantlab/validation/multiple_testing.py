"""Corrección por múltiples comparaciones (Fase 10 residual)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from quantlab.core.exceptions import ValidationError

AdjustMethod = Literal["bonferroni", "holm", "fdr_bh"]


@dataclass(frozen=True, slots=True)
class MultipleTestingResult:
    method: str
    alpha: float
    p_values: tuple[float, ...]
    adjusted: tuple[float, ...]
    rejected: tuple[bool, ...]


def _validate_p(p_values: Sequence[float], alpha: float = 0.05) -> tuple[float, ...]:
    if not p_values:
        raise ValidationError("p_values vacío")
    if not (0.0 < alpha < 1.0):
        raise ValidationError("alpha debe estar en (0, 1)")
    out: list[float] = []
    for p in p_values:
        pf = float(p)
        if pf < 0.0 or pf > 1.0:
            raise ValidationError("p_values deben estar en [0, 1]")
        out.append(pf)
    return tuple(out)


def adjust_pvalues(
    pvalues: Sequence[float],
    method: AdjustMethod | str = "bonferroni",
) -> tuple[float, ...]:
    """Ajusta p-valores: ``bonferroni`` | ``holm`` | ``fdr_bh``."""
    key = str(method).lower().strip()
    if key == "bonferroni":
        return bonferroni(pvalues).adjusted
    if key == "holm":
        return holm_bonferroni(pvalues).adjusted
    if key in ("fdr_bh", "bh", "benjamini_hochberg"):
        return benjamini_hochberg(pvalues).adjusted
    raise ValidationError(
        "method debe ser 'bonferroni' | 'holm' | 'fdr_bh'"
    )


def filter_significant(
    labels: Sequence[str],
    pvalues: Sequence[float],
    *,
    method: AdjustMethod | str = "bonferroni",
    alpha: float = 0.05,
) -> tuple[str, ...]:
    """Retorna labels con p ajustado <= alpha (control Error Tipo I)."""
    if len(labels) != len(pvalues):
        raise ValidationError("labels y pvalues deben tener igual longitud")
    _validate_p(pvalues, alpha)
    adjusted = adjust_pvalues(pvalues, method=method)
    return tuple(label for label, p_adj in zip(labels, adjusted, strict=True) if p_adj <= alpha)


def bonferroni(p_values: Sequence[float], *, alpha: float = 0.05) -> MultipleTestingResult:
    """Ajuste Bonferroni: p_adj = min(1, p * m)."""
    ps = _validate_p(p_values, alpha)
    m = len(ps)
    adjusted = tuple(min(1.0, p * m) for p in ps)
    rejected = tuple(a <= alpha for a in adjusted)
    return MultipleTestingResult(
        method="bonferroni",
        alpha=alpha,
        p_values=ps,
        adjusted=adjusted,
        rejected=rejected,
    )


def holm_bonferroni(p_values: Sequence[float], *, alpha: float = 0.05) -> MultipleTestingResult:
    """Holm–Bonferroni step-down."""
    ps = _validate_p(p_values, alpha)
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        # p * (m - rank)
        cand = min(1.0, ps[idx] * (m - rank))
        running = max(running, cand)
        adjusted[idx] = running
    rejected = tuple(a <= alpha for a in adjusted)
    return MultipleTestingResult(
        method="holm",
        alpha=alpha,
        p_values=ps,
        adjusted=tuple(adjusted),
        rejected=rejected,
    )


def benjamini_hochberg(
    p_values: Sequence[float], *, alpha: float = 0.05
) -> MultipleTestingResult:
    """FDR Benjamini–Hochberg."""
    ps = _validate_p(p_values, alpha)
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    adjusted = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        idx = order[rank - 1]
        cand = min(1.0, ps[idx] * m / rank)
        running = min(running, cand)
        adjusted[idx] = running
    rejected = tuple(a <= alpha for a in adjusted)
    return MultipleTestingResult(
        method="benjamini_hochberg",
        alpha=alpha,
        p_values=ps,
        adjusted=tuple(adjusted),
        rejected=rejected,
    )
