"""Integración traditional_score + kronos_score → final_score."""

from __future__ import annotations

from typing import Any

from quantlab.research.alpha.kronos.metrics import KronosMetrics, profile_kronos_score


def blend_scores(
    traditional_score: float,
    kronos_score: float | None,
    weight: float,
) -> tuple[float, float | None, float]:
    """Devuelve (traditional, kronos|None, final).

    Si kronos_score is None o weight<=0 → final = traditional (sin fingir 0).
    final = (1-w)*traditional + w*kronos
    """
    trad = float(traditional_score)
    if kronos_score is None or weight <= 0.0:
        return trad, None, trad
    w = max(0.0, min(1.0, float(weight)))
    k = float(kronos_score)
    final = (1.0 - w) * trad + w * k
    return trad, k, float(final)


def build_score_fields(
    *,
    traditional_score: float,
    metrics: KronosMetrics | None,
    profile: str,
    weight: float,
    applied: bool,
    skip_reason: str | None = None,
) -> dict[str, Any]:
    """Campos a fusionar en cada fila del Scanner."""
    kronos_score: float | None = None
    if applied and metrics is not None:
        kronos_score = profile_kronos_score(metrics, profile)
    trad, k_score, final = blend_scores(traditional_score, kronos_score, weight)
    out: dict[str, Any] = {
        "traditional_score": trad,
        "kronos_score": k_score,
        "final_score": final,
        "composite": final,  # ranking usa composite; UI muestra los tres
        "kronos_weight": weight if k_score is not None else 0.0,
        "kronos_applied": bool(k_score is not None),
        "kronos_skip_reason": skip_reason if k_score is None else None,
    }
    if metrics is not None:
        out["kronos_metrics"] = metrics.to_dict()
    else:
        out["kronos_metrics"] = None
    return out


def brief_explanation(
    *,
    symbol: str,
    profile: str,
    traditional_score: float,
    kronos_score: float | None,
    final_score: float,
    metrics: KronosMetrics | None,
    rank_improved: bool | None = None,
) -> str:
    """Texto accionable (estrategia a probar, no garantía)."""
    fam = profile.replace("_", " ")
    if kronos_score is None or metrics is None:
        return (
            f"{symbol}: ranking por score tradicional ({traditional_score:.3f}). "
            f"Kronos no aplicado. Estrategia compatible a probar: {fam}."
        )
    br = metrics.kronos_breakout_risk
    rp = metrics.kronos_range_probability
    disp = metrics.kronos_forecast_dispersion
    vol = metrics.kronos_forecast_volatility
    conf = metrics.kronos_confidence
    parts = [
        f"{symbol} score final {final_score:.3f} "
        f"(tradicional {traditional_score:.3f} + Kronos {kronos_score:.3f})."
    ]
    if rank_improved is False and traditional_score > final_score:
        parts.append(
            "Penalizada vs score actual porque Kronos estima "
            f"dispersión={disp:.3f}, riesgo de ruptura={br:.2f} "
            f"y vol futura={vol:.4f}."
        )
    else:
        parts.append(
            f"Kronos: rango={rp:.2f}, ruptura={br:.2f}, "
            f"estabilidad={metrics.kronos_regime_stability:.2f}, "
            f"confianza(acuerdo)={conf:.2f} (no calibrada)."
        )
    parts.append(f"Estrategia compatible a probar: {fam} (no es garantía).")
    return " ".join(parts)


__all__ = ["blend_scores", "brief_explanation", "build_score_fields"]
