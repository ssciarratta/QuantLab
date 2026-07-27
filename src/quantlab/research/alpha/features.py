"""FeatureCalculator modular para Alpha Scanner (FASE 3).

Ausencia de datos → ``None`` (nunca fingir 0 como “disponible”).
Los factores legacy (volatility / volume / liquidity) replican las fórmulas
de ``AlphaScanner`` para compatibilidad; el scoring default sigue en legacy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Any

from quantlab.core.types.market import Bar


@dataclass(frozen=True, slots=True)
class MarketExtras:
    """Datos opcionales de mercado (book / funding / OI)."""

    best_bid: float | None = None
    best_ask: float | None = None
    depth_notional: float | None = None
    funding_rate: float | None = None
    open_interest: float | None = None


@dataclass(frozen=True, slots=True)
class FeatureVector:
    instrument_id: str
    # Legacy (mismas fórmulas que AlphaScanner)
    volatility: float | None
    volume_score: float | None
    liquidity_score: float | None
    # Extendidos
    momentum: float | None
    trend_quality: float | None
    spread: float | None
    depth: float | None
    volume_quality: float | None
    volatility_quality: float | None
    funding: float | None
    open_interest: float | None
    persistence: float | None
    n_bars: int
    n_live_bars: int

    def available_map(self) -> dict[str, bool]:
        return {
            "volatility": self.volatility is not None,
            "volume_score": self.volume_score is not None,
            "liquidity_score": self.liquidity_score is not None,
            "momentum": self.momentum is not None,
            "trend_quality": self.trend_quality is not None,
            "spread": self.spread is not None,
            "depth": self.depth is not None,
            "volume_quality": self.volume_quality is not None,
            "volatility_quality": self.volatility_quality is not None,
            "funding": self.funding is not None,
            "open_interest": self.open_interest is not None,
            "persistence": self.persistence is not None,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "volatility": self.volatility,
            "volume_score": self.volume_score,
            "liquidity_score": self.liquidity_score,
            "momentum": self.momentum,
            "trend_quality": self.trend_quality,
            "spread": self.spread,
            "depth": self.depth,
            "volume_quality": self.volume_quality,
            "volatility_quality": self.volatility_quality,
            "funding": self.funding,
            "open_interest": self.open_interest,
            "persistence": self.persistence,
            "n_bars": self.n_bars,
            "n_live_bars": self.n_live_bars,
            "available": self.available_map(),
        }


def _live_bars(bars: Sequence[Bar]) -> list[Bar]:
    live = [b for b in bars if b.volume > 0]
    return live or list(bars)


def _returns(closes: Sequence[float]) -> list[float]:
    out: list[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev == 0:
            continue
        out.append((closes[i] - prev) / prev)
    return out


def _legacy_triple(bars: Sequence[Bar]) -> tuple[float | None, float | None, float | None]:
    """Replica AlphaScanner: vol=pstdev(rets), volume=mean(vol), liq=1/(avg_range+1e-9)."""
    if not bars:
        return None, None, None
    base = _live_bars(bars)
    closes = [float(b.close) for b in base]
    volumes = [float(b.volume) for b in base]
    ranges = [
        float((b.high - b.low) / b.close) if b.close > 0 else 0.0 for b in base
    ]
    rets = _returns(closes)
    # Compat legacy: <2 retornos → volatility=0.0 (no None) para no romper baseline
    vol = float(pstdev(rets)) if len(rets) > 1 else 0.0
    volume_score = float(mean(volumes)) if volumes else 0.0
    avg_range = float(mean(ranges)) if ranges else 1.0
    liquidity_score = 1.0 / (avg_range + 1e-9)
    return vol, volume_score, liquidity_score


def _momentum(closes: Sequence[float]) -> float | None:
    if len(closes) < 2 or closes[0] == 0:
        return None
    return (closes[-1] / closes[0]) - 1.0


def _trend_quality(closes: Sequence[float]) -> float | None:
    """|corr(t, close)| en [0,1]; None si no hay varianza."""
    n = len(closes)
    if n < 3:
        return None
    xs = list(range(n))
    mean_x = (n - 1) / 2.0
    mean_y = mean(closes)
    var_y = sum((y - mean_y) ** 2 for y in closes)
    if var_y <= 0:
        return None
    var_x = sum((x - mean_x) ** 2 for x in xs)
    cov = sum((xs[i] - mean_x) * (closes[i] - mean_y) for i in range(n))
    denom = (var_x * var_y) ** 0.5
    if denom <= 0:
        return None
    return float(abs(cov / denom))


def _spread(
    bars: Sequence[Bar],
    extras: MarketExtras | None,
) -> float | None:
    if extras is not None and extras.best_bid is not None and extras.best_ask is not None:
        mid = (extras.best_bid + extras.best_ask) / 2.0
        if mid <= 0:
            return None
        return (extras.best_ask - extras.best_bid) / mid
    # Proxy HL/C (documentado como proxy, no book)
    base = _live_bars(bars)
    if not base:
        return None
    ranges = [
        float((b.high - b.low) / b.close) if b.close > 0 else None for b in base
    ]
    clean = [r for r in ranges if r is not None]
    if not clean:
        return None
    return float(mean(clean))


def _volume_quality(bars: Sequence[Bar]) -> float | None:
    if not bars:
        return None
    live = sum(1 for b in bars if b.volume > 0)
    return live / len(bars)


def _volatility_quality(rets: Sequence[float]) -> float | None:
    if len(rets) < 2:
        return None
    # Más retornos → más confianza (saturado en 1 a ~30 samples)
    return min(1.0, (len(rets) - 1) / 30.0)


def _persistence(rets: Sequence[float]) -> float | None:
    if len(rets) < 3:
        return None
    x = rets[:-1]
    y = rets[1:]
    mx, my = mean(x), mean(y)
    var_x = sum((v - mx) ** 2 for v in x)
    var_y = sum((v - my) ** 2 for v in y)
    if var_x <= 0 or var_y <= 0:
        return None
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(len(x)))
    return float(cov / ((var_x * var_y) ** 0.5))


class FeatureCalculator:
    """Calcula vector de features por instrumento (sin scoring)."""

    def compute(
        self,
        instrument_id: str,
        bars: Sequence[Bar],
        *,
        extras: MarketExtras | None = None,
    ) -> FeatureVector:
        ex = extras or MarketExtras()
        base = _live_bars(bars) if bars else []
        closes = [float(b.close) for b in base]
        rets = _returns(closes)
        vol, volume_score, liquidity_score = _legacy_triple(bars)

        depth = ex.depth_notional  # None si no hay book depth
        funding = ex.funding_rate
        oi = ex.open_interest

        return FeatureVector(
            instrument_id=instrument_id,
            volatility=vol if bars else None,
            volume_score=volume_score if bars else None,
            liquidity_score=liquidity_score if bars else None,
            momentum=_momentum(closes),
            trend_quality=_trend_quality(closes),
            spread=_spread(bars, extras),
            depth=depth,
            volume_quality=_volume_quality(bars),
            volatility_quality=_volatility_quality(rets),
            funding=funding,
            open_interest=oi,
            persistence=_persistence(rets),
            n_bars=len(bars),
            n_live_bars=len(base),
        )

    def compute_many(
        self,
        bars_by_instrument: Mapping[str, Sequence[Bar]],
        *,
        extras_by_instrument: Mapping[str, MarketExtras] | None = None,
    ) -> dict[str, FeatureVector]:
        extras_map = dict(extras_by_instrument or {})
        return {
            iid: self.compute(iid, bars, extras=extras_map.get(iid))
            for iid, bars in bars_by_instrument.items()
        }


__all__ = [
    "FeatureCalculator",
    "FeatureVector",
    "MarketExtras",
]
