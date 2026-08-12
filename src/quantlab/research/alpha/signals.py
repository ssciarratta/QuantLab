"""Helpers para IDs deterministas de señales Alpha."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from quantlab.research.alpha.models import SignalScope


def stable_signal_id(
    *,
    signal_type: str,
    scope: SignalScope,
    symbols: tuple[str, ...],
    timestamp: datetime,
    raw_score: float,
    lag: int | None,
    lookback: int,
) -> str:
    """Hash estable para deduplicar/persistir señales."""
    payload = {
        "signal_type": signal_type,
        "scope": scope.value,
        "symbols": sorted(symbols),
        "timestamp": timestamp.isoformat(),
        "raw_score": round(raw_score, 12),
        "lag": lag,
        "lookback": lookback,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return digest[:32]
