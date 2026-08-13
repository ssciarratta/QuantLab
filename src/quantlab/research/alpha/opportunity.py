"""Identidad de oportunidad (Ranking A) y helpers temporales de validación."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from quantlab.research.alpha.models import AlphaSignal

_PERIODS_PER_YEAR: dict[str, float] = {
    "1m": 525_600.0,
    "3m": 175_200.0,
    "5m": 105_120.0,
    "15m": 35_040.0,
    "30m": 17_520.0,
    "1h": 8_760.0,
    "2h": 4_380.0,
    "4h": 2_190.0,
    "6h": 1_460.0,
    "8h": 1_095.0,
    "12h": 730.0,
    "1d": 365.0,
    "1w": 52.0,
}


def make_opportunity_id(
    *,
    signal: AlphaSignal,
    scan_id: str | None = None,
    venue: str | None = None,
    market_type: str | None = None,
) -> str:
    """Hash estable de la detección (no de la estrategia)."""
    payload: dict[str, Any] = {
        "scan_id": scan_id or "",
        "signal_id": signal.signal_id,
        "scope": signal.scope.value,
        "symbols": list(signal.symbols),
        "signal_type": signal.signal_type,
        "timeframe": signal.timeframe,
        "lookback": signal.lookback,
        "lag": signal.lag,
        "venue": venue or (signal.metadata or {}).get("venue") or "",
        "market_type": market_type or (signal.metadata or {}).get("market_type") or "",
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return "opp_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def periods_per_year_for_timeframe(timeframe: str) -> float:
    key = (timeframe or "1h").strip().lower()
    return float(_PERIODS_PER_YEAR.get(key, 8_760.0))


def effective_embargo_bars(
    *,
    requested: int,
    lookback: int,
    n_bars: int = 0,
    train_fraction: float = 0.70,
) -> int:
    """Embargo ≥2; lookback corto puede subir hasta 8; nunca vacía el test."""
    base = max(2, int(requested))
    if 0 < lookback < 50:
        base = max(base, min(int(lookback), 8))
    if n_bars > 0:
        cut = int(n_bars * train_fraction)
        cut = max(1, min(cut, n_bars - 1))
        for min_test in (6, 4):
            max_embargo = n_bars - cut - min_test
            if max_embargo >= 0:
                return max(0, min(base, max_embargo))
        return 0
    return base


def ranking_b_status(*, validated: bool, ok: bool) -> str:
    if not ok:
        return "failed"
    if validated:
        return "validated_historically"
    return "rejected"


__all__ = [
    "effective_embargo_bars",
    "make_opportunity_id",
    "periods_per_year_for_timeframe",
    "ranking_b_status",
]
