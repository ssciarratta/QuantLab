"""Estadísticas para análisis pairwise (sin scipy)."""

from __future__ import annotations

import math


def ols_hedge_ratio(y: list[float], x: list[float]) -> float:
    """Regresión y ~ x → beta (hedge ratio)."""
    n = min(len(y), len(x))
    if n < 4:
        return 1.0
    mx = sum(x[:n]) / n
    my = sum(y[:n]) / n
    var_x = sum((x[i] - mx) ** 2 for i in range(n))
    if var_x <= 0:
        return 1.0
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    return cov / var_x


def log_spread(closes_a: list[float], closes_b: list[float], beta: float) -> list[float]:
    n = min(len(closes_a), len(closes_b))
    out: list[float] = []
    for i in range(n):
        ca, cb = closes_a[i], closes_b[i]
        if ca <= 0 or cb <= 0:
            continue
        out.append(math.log(ca) - beta * math.log(cb))
    return out


def spread_zscore(spread: list[float], window: int) -> list[float]:
    if len(spread) < window:
        return []
    out: list[float] = []
    for i in range(window - 1, len(spread)):
        w = spread[i - window + 1 : i + 1]
        mu = sum(w) / len(w)
        var = sum((v - mu) ** 2 for v in w) / max(1, len(w) - 1)
        std = math.sqrt(var) if var > 0 else 1e-12
        out.append((spread[i] - mu) / std)
    return out


def adf_pvalue_proxy(spread: list[float]) -> float:
    """Proxy ADF: t-stat AR(1) vs critical ~ -2.86 (5% univariado)."""
    if len(spread) < 20:
        return 1.0
    y = spread[1:]
    x = spread[:-1]
    n = len(y)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    den = sum((x[i] - mx) ** 2 for i in range(n))
    if den <= 0:
        return 1.0
    b = num / den
    a = my - b * mx
    resid = [y[i] - (a + b * x[i]) for i in range(n)]
    sse = sum(r * r for r in resid)
    se_b = math.sqrt(sse / max(1, n - 2) / den) if den > 0 else 1e12
    t_stat = b / se_b if se_b > 0 else 0.0
    # b < 1 estacionario; t más negativo → más estacionario
    if b >= 1.0:
        return 1.0
    z = abs(t_stat + 2.86)
    return min(1.0, math.exp(-0.5 * z * z))


def half_life_bars(spread: list[float]) -> float | None:
    """Half-life mean-reversion AR(1) sobre spread."""
    if len(spread) < 10:
        return None
    y = spread[1:]
    x = spread[:-1]
    n = len(y)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    den = sum((x[i] - mx) ** 2 for i in range(n))
    if den <= 0:
        return None
    b = num / den
    if b <= 0 or b >= 1:
        return None
    return -math.log(2) / math.log(b)
