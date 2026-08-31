"""Ensambla features desde AlphaSignal / dicts persistidos (sin barras crudas)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from quantlab.research.alpha.models import AlphaSignal

FEATURE_SCHEMA_VERSION = "ml-features-v1"

# Orden estable numérico (LightGBM / stub).
NUMERIC_FEATURE_KEYS: tuple[str, ...] = (
    "norm_score",
    "confidence",
    "lag",
    "n_symbols",
    "lookback",
    "comp_volatility",
    "comp_volume",
    "comp_liquidity",
    "comp_momentum",
    "comp_trend_quality",
    "comp_spread",
    "comp_depth",
    "comp_funding",
    "comp_open_interest",
    "comp_persistence",
    "meta_hedge_ratio",
    "meta_adf_pvalue",
    "meta_half_life",
    "meta_spread_z",
    "meta_estimated_cost_bps",
)

CATEGORICAL_FEATURE_KEYS: tuple[str, ...] = (
    "signal_type",
    "scope",
    "timeframe",
    "market_type",
    "profile",
)


def _f(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _comp_map(payload: Mapping[str, Any]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    comps = payload.get("components")
    if isinstance(comps, list):
        for c in comps:
            if not isinstance(c, Mapping):
                continue
            name = str(c.get("name") or "")
            if not name:
                continue
            # volume_score legacy → volume
            key = name.replace("_score", "")
            out[key] = _f(c.get("normalized"))
    meta = payload.get("metadata")
    if isinstance(meta, Mapping):
        # a veces components viven en metadata
        pass
    return out


def signal_to_feature_row(signal: AlphaSignal | Mapping[str, Any]) -> dict[str, Any]:
    """Fila feature schema v1. Missing → None (no fingir 0)."""
    d = signal.to_dict() if isinstance(signal, AlphaSignal) else dict(signal)
    raw_meta = d.get("metadata")
    meta = raw_meta if isinstance(raw_meta, Mapping) else {}
    comps = _comp_map(d)
    # components also from metadata.components
    if isinstance(meta.get("components"), list):
        for c in meta["components"]:  # type: ignore[index]
            if isinstance(c, Mapping) and c.get("name"):
                comps[str(c["name"]).replace("_score", "")] = _f(c.get("normalized"))

    scope = str(d.get("scope") or "individual")
    norm = _f(d.get("normalized_score"))
    if norm is None:
        norm = _f(d.get("raw_score"))

    row: dict[str, Any] = {
        "norm_score": norm,
        "confidence": _f(d.get("confidence")),
        "lag": float(d["lag"]) if d.get("lag") is not None else None,
        "n_symbols": float(len(d.get("symbols") or [])),
        "lookback": _f(d.get("lookback")) or 0.0,
        "comp_volatility": comps.get("volatility"),
        "comp_volume": comps.get("volume") if comps.get("volume") is not None else comps.get(
            "volume_score"
        ),
        "comp_liquidity": comps.get("liquidity")
        if comps.get("liquidity") is not None
        else comps.get("liquidity_score"),
        "comp_momentum": comps.get("momentum"),
        "comp_trend_quality": comps.get("trend_quality"),
        "comp_spread": comps.get("spread"),
        "comp_depth": comps.get("depth"),
        "comp_funding": comps.get("funding"),
        "comp_open_interest": comps.get("open_interest"),
        "comp_persistence": comps.get("persistence"),
        "meta_hedge_ratio": _f(meta.get("hedge_ratio")),
        "meta_adf_pvalue": _f(meta.get("adf_pvalue")),
        "meta_half_life": _f(meta.get("half_life")),
        "meta_spread_z": _f(meta.get("spread_z")),
        "meta_estimated_cost_bps": _f(meta.get("estimated_cost_bps")),
        "signal_type": str(d.get("signal_type") or ""),
        "scope": scope,
        "timeframe": str(d.get("timeframe") or "1h"),
        "market_type": str(meta.get("market_type") or d.get("market_type") or "spot"),
        "profile": str(meta.get("profile") or d.get("signal_type") or ""),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
    }
    return row


def feature_row_to_vector(
    row: Mapping[str, Any],
    *,
    category_maps: Mapping[str, Mapping[str, int]] | None = None,
) -> list[float]:
    """Vector numérico fijo; categoricals → int (mapa o hash estable)."""
    maps = category_maps or {}
    vec: list[float] = []
    for k in NUMERIC_FEATURE_KEYS:
        v = row.get(k)
        vec.append(float("nan") if v is None else float(v))
    for k in CATEGORICAL_FEATURE_KEYS:
        raw = str(row.get(k) or "")
        m = maps.get(k)
        if m is not None and raw in m:
            vec.append(float(m[raw]))
        else:
            # hash estable 0..99
            vec.append(float(sum(ord(c) for c in raw) % 100) if raw else float("nan"))
    return vec


def build_category_maps(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    maps: dict[str, dict[str, int]] = {k: {} for k in CATEGORICAL_FEATURE_KEYS}
    for row in rows:
        for k in CATEGORICAL_FEATURE_KEYS:
            raw = str(row.get(k) or "")
            if raw and raw not in maps[k]:
                maps[k][raw] = len(maps[k])
    return maps


__all__ = [
    "CATEGORICAL_FEATURE_KEYS",
    "FEATURE_SCHEMA_VERSION",
    "NUMERIC_FEATURE_KEYS",
    "build_category_maps",
    "feature_row_to_vector",
    "signal_to_feature_row",
]
