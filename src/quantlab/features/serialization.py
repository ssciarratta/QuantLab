"""Serialización determinista de FeatureFrame / FeatureSeries."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.features.contracts import FeatureFrame, FeaturePoint, FeatureSeries


def feature_point_to_dict(point: FeaturePoint) -> dict[str, Any]:
    return {
        "timestamp": point.timestamp.isoformat(),
        "instrument_id": point.instrument_id,
        "name": point.name,
        "value": str(point.value),
        "lookback_used": point.lookback_used,
        "metadata": dict(point.metadata) if point.metadata is not None else None,
    }


def feature_series_to_dict(series: FeatureSeries) -> dict[str, Any]:
    return {
        "name": series.name,
        "schema_version": series.schema_version,
        "min_lookback": series.min_lookback,
        "points": [feature_point_to_dict(p) for p in series.points],
    }


def feature_frame_to_dict(frame: FeatureFrame) -> dict[str, Any]:
    return {
        "instrument_id": frame.instrument_id,
        "schema_version": frame.schema_version,
        "min_lookback": frame.min_lookback,
        "bar_count": frame.bar_count,
        "pipeline_name": frame.pipeline_name,
        "series": {
            name: feature_series_to_dict(frame.series[name]) for name in sorted(frame.series.keys())
        },
    }


def feature_point_from_dict(data: dict[str, Any]) -> FeaturePoint:
    meta = data.get("metadata")
    return FeaturePoint(
        timestamp=datetime.fromisoformat(str(data["timestamp"])),
        instrument_id=str(data["instrument_id"]),
        name=str(data["name"]),
        value=Decimal(str(data["value"])),
        lookback_used=int(data["lookback_used"]),
        metadata=dict(meta) if isinstance(meta, dict) else None,
    )


def feature_series_from_dict(data: dict[str, Any]) -> FeatureSeries:
    points_raw = data.get("points")
    if not isinstance(points_raw, list):
        raise ValidationError("FeatureSeries.points inválido")
    points_list: list[FeaturePoint] = []
    for p in points_raw:
        if not isinstance(p, dict):
            raise ValidationError("FeatureSeries.points contiene entrada no-dict")
        points_list.append(feature_point_from_dict(p))
    return FeatureSeries(
        name=str(data["name"]),
        schema_version=str(data["schema_version"]),
        points=tuple(points_list),
        min_lookback=int(data["min_lookback"]),
    )


def feature_frame_from_dict(data: dict[str, Any]) -> FeatureFrame:
    series_raw = data.get("series")
    if not isinstance(series_raw, dict):
        raise ValidationError("FeatureFrame.series inválido")
    series: dict[str, FeatureSeries] = {}
    for k, v in series_raw.items():
        if not isinstance(v, dict):
            raise ValidationError(f"FeatureFrame.series[{k!r}] no es dict")
        series[str(k)] = feature_series_from_dict(v)
    return FeatureFrame(
        instrument_id=str(data["instrument_id"]),
        schema_version=str(data["schema_version"]),
        series=series,
        min_lookback=int(data["min_lookback"]),
        bar_count=int(data["bar_count"]),
        pipeline_name=str(data["pipeline_name"]),
    )
