"""Dataset supervisado: features(t) ↔ label validated desde alpha_trials."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.research.alpha.ml.features import (
    FEATURE_SCHEMA_VERSION,
    build_category_maps,
    feature_row_to_vector,
    signal_to_feature_row,
)
from quantlab.research.alpha.models import AlphaSignal, SignalDirection, SignalScope
from quantlab.research.alpha.validation.trial_ledger import TrialLedger


@dataclass(frozen=True, slots=True)
class MlDataset:
    """Filas ordenadas por timestamp."""

    feature_rows: tuple[dict[str, Any], ...]
    labels: tuple[int, ...]
    timestamps: tuple[datetime, ...]
    feature_schema_version: str = FEATURE_SCHEMA_VERSION
    target_name: str = "validated_next_window"
    default_strategy_id: str = "momentum"

    def n_pos(self) -> int:
        return sum(self.labels)

    def n_neg(self) -> int:
        return len(self.labels) - self.n_pos()


def trials_to_labeled_rows(
    ledger: TrialLedger,
    *,
    default_strategy_id: str = "momentum",
) -> list[dict[str, Any]]:
    """Cada trial de validación → fila con y=validated (solo phase=validation)."""
    rows: list[dict[str, Any]] = []
    for rec in ledger.records():
        meta = rec.metadata or {}
        if meta.get("phase") != "validation":
            continue
        # Target: validated, NUNCA retorno bruto
        if "validated" not in meta and "sharpe_net" in meta and "returns" in meta:
            raise ValidationError("target ilegal: no usar returns como label")
        y = 1 if meta.get("validated") is True else 0
        # Feature proxy desde metadata del trial + signal fields (sin métricas de outcome)
        sel_raw = meta.get("selection_raw_score")
        sel_norm = meta.get("selection_normalized_score")
        if sel_raw is None and sel_norm is None:
            # sin score de selección: usar confidence/lag proxies, raw_score=0.5 neutro
            sel_raw = 0.5
        sig_like: dict[str, Any] = {
            "signal_id": meta.get("signal_id") or rec.trial_id,
            "timestamp": rec.created_at or datetime.now(tz=UTC).isoformat(),
            "signal_type": rec.signal_type,
            "scope": "pair" if len(rec.symbols) == 2 else "individual",
            "symbols": list(rec.symbols),
            "direction": "long-short" if len(rec.symbols) == 2 else "long",
            "raw_score": float(sel_raw if sel_raw is not None else 0.5),
            "normalized_score": float(sel_norm) if sel_norm is not None else None,
            "confidence": meta.get("confidence"),
            "lookback": rec.lookback,
            "lag": rec.lag,
            "timeframe": meta.get("timeframe") or "1h",
            "metadata": {
                k: meta.get(k)
                for k in (
                    "hedge_ratio",
                    "adf_pvalue",
                    "half_life",
                    "spread_z",
                    "estimated_cost_bps",
                    "market_type",
                    "profile",
                    "components",
                )
                if k in meta
            },
        }
        feat = signal_to_feature_row(sig_like)
        ts_raw = rec.created_at
        try:
            ts = datetime.fromisoformat(ts_raw) if ts_raw else datetime.now(tz=UTC)
        except ValueError:
            ts = datetime.now(tz=UTC)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        rows.append(
            {
                "features": feat,
                "y": y,
                "timestamp": ts,
                "strategy_id": meta.get("strategy_id") or default_strategy_id,
                "trial_id": rec.trial_id,
            }
        )
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def build_dataset_from_trials(
    ledger: TrialLedger,
    *,
    default_strategy_id: str = "momentum",
    min_rows: int = 1,
) -> MlDataset:
    rows = trials_to_labeled_rows(ledger, default_strategy_id=default_strategy_id)
    if len(rows) < min_rows:
        raise ValidationError(
            f"dataset ML insuficiente: {len(rows)} filas (min={min_rows}); "
            "bootstrap labels o corré más validate_candidate"
        )
    return MlDataset(
        feature_rows=tuple(r["features"] for r in rows),
        labels=tuple(int(r["y"]) for r in rows),
        timestamps=tuple(r["timestamp"] for r in rows),
        default_strategy_id=default_strategy_id,
    )


def make_synthetic_dataset(
    *,
    n: int = 80,
    n_pos: int = 25,
    seed: int = 7,
) -> MlDataset:
    """Fixture reproducible para tests / train smoke (sin LIVE)."""
    if n_pos >= n or n_pos < 1:
        raise ValidationError("n_pos debe estar en [1, n)")
    rng_state = seed
    rows: list[dict[str, Any]] = []
    labels: list[int] = []
    stamps: list[datetime] = []
    base = datetime(2024, 1, 1, tzinfo=UTC)
    pos_idx = set(range(0, n, max(1, n // n_pos))) 
    # ensure exactly ~n_pos
    pos_list = sorted(pos_idx)[:n_pos]
    while len(pos_list) < n_pos:
        pos_list.append(len(pos_list) % n)
    pos_set = set(pos_list[:n_pos])

    for i in range(n):
        rng_state = (1103515245 * rng_state + 12345) % (2**31)
        u = (rng_state % 1000) / 1000.0
        y = 1 if i in pos_set else 0
        # Señal sintética: positivos tienden a norm_score alto
        norm = (0.55 + 0.4 * u) if y == 1 else (0.05 + 0.45 * u)
        sig = AlphaSignal(
            signal_id=f"syn-{i}",
            timestamp=base + timedelta(hours=i),
            signal_type="legacy_v1" if i % 2 == 0 else "lagged_correlation",
            scope=SignalScope.INDIVIDUAL if i % 3 else SignalScope.PAIR,
            symbols=("BN:BTCUSDT",) if i % 3 else ("BN:BTCUSDT", "BN:ETHUSDT"),
            direction=SignalDirection.LONG if i % 3 else SignalDirection.LONG_SHORT,
            raw_score=norm,
            confidence=0.5 + 0.4 * u,
            lookback=24,
            lag=(i % 5) if i % 3 == 0 else None,
            timeframe="1h",
            normalized_score=norm,
            metadata={
                "market_type": "spot",
                "hedge_ratio": 0.5 + u * 0.2 if i % 3 == 0 else None,
                "adf_pvalue": 0.01 + u * 0.2 if i % 3 == 0 else None,
                "components": [
                    {"name": "volatility", "normalized": u, "available": True},
                    {"name": "momentum", "normalized": norm, "available": True},
                ],
            },
        )
        rows.append(signal_to_feature_row(sig))
        labels.append(y)
        stamps.append(sig.timestamp)
    return MlDataset(
        feature_rows=tuple(rows),
        labels=tuple(labels),
        timestamps=tuple(stamps),
    )


def dataset_to_matrix(
    ds: MlDataset,
) -> tuple[list[list[float]], list[int], dict[str, dict[str, int]]]:
    maps = build_category_maps(ds.feature_rows)
    x = [feature_row_to_vector(r, category_maps=maps) for r in ds.feature_rows]
    return x, list(ds.labels), maps


def save_dataset_json(ds: MlDataset, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "feature_schema_version": ds.feature_schema_version,
        "target_name": ds.target_name,
        "default_strategy_id": ds.default_strategy_id,
        "rows": [
            {
                "features": ds.feature_rows[i],
                "y": ds.labels[i],
                "timestamp": ds.timestamps[i].isoformat(),
            }
            for i in range(len(ds.labels))
        ],
    }
    path.write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")


def load_dataset_json(path: Path) -> MlDataset:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = list(raw.get("rows") or [])
    feats: list[dict[str, Any]] = []
    labels: list[int] = []
    stamps: list[datetime] = []
    for r in rows:
        feats.append(dict(r["features"]))
        labels.append(int(r["y"]))
        stamps.append(datetime.fromisoformat(str(r["timestamp"])))
    return MlDataset(
        feature_rows=tuple(feats),
        labels=tuple(labels),
        timestamps=tuple(stamps),
        feature_schema_version=str(raw.get("feature_schema_version") or FEATURE_SCHEMA_VERSION),
        target_name=str(raw.get("target_name") or "validated_next_window"),
        default_strategy_id=str(raw.get("default_strategy_id") or "momentum"),
    )


__all__ = [
    "MlDataset",
    "build_dataset_from_trials",
    "dataset_to_matrix",
    "load_dataset_json",
    "make_synthetic_dataset",
    "save_dataset_json",
    "trials_to_labeled_rows",
]
