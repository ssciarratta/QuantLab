"""Métricas interpretables a partir de trayectorias OHLCV (stdlib only).

Definiciones (K trayectorias, horizonte H):

- kronos_forecast_volatility: mean_k(std(log-returns de la traj k))
- kronos_forecast_dispersion: std_k(c_{k,H}) / (|mean_k(c_{k,H})|+eps)
- kronos_breakout_risk: fracción con max(high)>R_high o min(low)<R_low
- kronos_trend_risk: mean_k(|corr(t, c_k)|)
- kronos_range_probability: fracción con closes ⊆ [R_low, R_high]
- kronos_regime_stability: 1/(1+σ̂+D̂)
- kronos_confidence: 1/(1+CV_k(c_{k,H})) — acuerdo; NO probabilidad calibrada
- kronos_market_making_score: mezcla rango/ruptura/tendencia/confianza − pen_vol
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from statistics import mean, pstdev
from typing import Any

from quantlab.research.alpha.kronos.protocol import TrajectoryBatch

_EPS = 1e-12


@dataclass(frozen=True, slots=True)
class KronosMetrics:
    kronos_forecast_volatility: float | None
    kronos_forecast_dispersion: float | None
    kronos_breakout_risk: float | None
    kronos_trend_risk: float | None
    kronos_range_probability: float | None
    kronos_regime_stability: float | None
    kronos_confidence: float | None
    kronos_market_making_score: float | None
    confidence_is_calibrated_probability: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["note"] = (
            "kronos_confidence mide acuerdo entre trayectorias; "
            "NO es una probabilidad calibrada de acierto."
        )
        return d


def _corr(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2 or len(ys) != n:
        return 0.0
    mx = mean(xs)
    my = mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x < _EPS or den_y < _EPS:
        return 0.0
    return num / (den_x * den_y)


def _log_return_std(closes: tuple[float, ...]) -> float:
    if len(closes) < 2:
        return 0.0
    rets: list[float] = []
    for i in range(1, len(closes)):
        a, b = closes[i - 1], closes[i]
        if a <= 0 or b <= 0:
            continue
        rets.append(math.log(b / a))
    if len(rets) < 2:
        return 0.0
    return float(pstdev(rets))


def compute_kronos_metrics(
    batch: TrajectoryBatch,
    *,
    range_high: float,
    range_low: float,
    ref_vol: float | None = None,
) -> KronosMetrics:
    if batch.n_samples < 1 or batch.horizon < 2:
        return KronosMetrics(None, None, None, None, None, None, None, None, False)

    k = batch.n_samples
    h = batch.horizon
    per_vols = [_log_return_std(batch.closes[i]) for i in range(k)]
    forecast_vol = float(mean(per_vols)) if per_vols else 0.0

    terminals = [batch.closes[i][-1] for i in range(k)]
    mean_t = float(mean(terminals))
    dispersion = float(pstdev(terminals) / (abs(mean_t) + _EPS)) if len(terminals) > 1 else 0.0

    breakouts = 0
    in_range = 0
    trend_vals: list[float] = []
    t_idx = [float(i) for i in range(h)]
    for i in range(k):
        hi = max(batch.highs[i])
        lo = min(batch.lows[i])
        if hi > range_high or lo < range_low:
            breakouts += 1
        path = batch.closes[i]
        if max(path) <= range_high and min(path) >= range_low:
            in_range += 1
        trend_vals.append(abs(_corr(t_idx, list(path))))

    breakout_risk = breakouts / k
    range_prob = in_range / k
    trend_risk = float(mean(trend_vals)) if trend_vals else 0.0

    if ref_vol and ref_vol > 0:
        vol_term = min(5.0, forecast_vol / (ref_vol + _EPS))
    else:
        vol_term = min(5.0, forecast_vol * 50.0)
    disp_term = min(5.0, dispersion * 10.0)
    stability = float(1.0 / (1.0 + vol_term + disp_term))

    cv = float(pstdev(terminals) / (abs(mean_t) + _EPS)) if len(terminals) > 1 else 0.0
    confidence = float(1.0 / (1.0 + cv))

    vol_pen = 0.0
    if forecast_vol > 0.08:
        vol_pen = min(0.25, (forecast_vol - 0.08) * 2.0)
    elif forecast_vol < 0.001:
        vol_pen = 0.05

    mm = (
        0.35 * range_prob
        + 0.25 * (1.0 - breakout_risk)
        + 0.20 * (1.0 - min(1.0, trend_risk))
        + 0.20 * confidence
        - vol_pen
    )
    mm = float(max(0.0, min(1.0, mm)))

    return KronosMetrics(
        kronos_forecast_volatility=forecast_vol,
        kronos_forecast_dispersion=dispersion,
        kronos_breakout_risk=breakout_risk,
        kronos_trend_risk=trend_risk,
        kronos_range_probability=range_prob,
        kronos_regime_stability=stability,
        kronos_confidence=confidence,
        kronos_market_making_score=mm,
        confidence_is_calibrated_probability=False,
    )


def profile_kronos_score(metrics: KronosMetrics, profile: str) -> float | None:
    if metrics.kronos_confidence is None:
        return None
    br = metrics.kronos_breakout_risk
    rp = metrics.kronos_range_probability
    tr = metrics.kronos_trend_risk
    disp = metrics.kronos_forecast_dispersion
    stab = metrics.kronos_regime_stability
    conf = metrics.kronos_confidence
    mm = metrics.kronos_market_making_score
    if None in (br, rp, tr, disp, stab, conf, mm):
        return None

    key = (profile or "").strip().lower()
    inv_disp = 1.0 / (1.0 + float(disp) * 10.0)
    inv_br = 1.0 - float(br)

    if key in ("market_making", "microstructure", "avellaneda_stoikov"):
        return float(mm)
    if key in ("mean_reversion", "mr", "mean-reversion"):
        return float(
            max(
                0.0,
                min(
                    1.0,
                    0.45 * float(rp)
                    + 0.25 * inv_br
                    + 0.20 * (1.0 - min(1.0, float(tr)))
                    + 0.10 * float(conf),
                ),
            )
        )
    if key in ("momentum", "trend"):
        return float(
            max(
                0.0,
                min(
                    1.0,
                    0.40 * min(1.0, float(tr))
                    + 0.35 * float(conf)
                    + 0.15 * float(stab)
                    + 0.10 * inv_disp,
                ),
            )
        )
    if key in ("balanced", "ml", "multi_asset", "options"):
        return float(
            max(
                0.0,
                min(
                    1.0,
                    0.40 * float(mm) + 0.30 * float(stab) + 0.20 * float(conf) + 0.10 * inv_disp,
                ),
            )
        )
    return float(stab)


__all__ = ["KronosMetrics", "compute_kronos_metrics", "profile_kronos_score"]
