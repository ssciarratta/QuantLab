"""Caché determinista por símbolo/TF/hash/params (JSON)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def forecast_cache_key(
    *,
    symbol: str,
    interval: str,
    model: str,
    lookback: int,
    pred_len: int,
    sample_count: int,
    temperature: float,
    top_p: float,
    seed: int,
    data_hash: str,
) -> str:
    raw = "|".join(
        [
            symbol,
            interval,
            model,
            str(lookback),
            str(pred_len),
            str(sample_count),
            f"{temperature:.6f}",
            f"{top_p:.6f}",
            str(seed),
            data_hash,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]


def hash_closes(closes: tuple[float, ...]) -> str:
    payload = ",".join(f"{c:.8f}" for c in closes)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


class KronosDiskCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict[str, Any] | None:
        path = self.root / f"{key}.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def set(self, key: str, payload: dict[str, Any]) -> None:
        path = self.root / f"{key}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")


__all__ = ["KronosDiskCache", "forecast_cache_key", "hash_closes"]
