"""Capa de features — depende de `core`, nunca al revés."""

from quantlab.features.contracts import (
    FeatureFrame,
    FeaturePoint,
    FeatureSeries,
    FeatureTransformer,
    Indicator,
)
from quantlab.features.indicators import (
    ATRIndicator,
    EMACloseIndicator,
    RSIWilderIndicator,
    SMACloseIndicator,
)
from quantlab.features.pipeline import FeaturePipeline, build_pipeline
from quantlab.features.store import FeatureStore, FeatureStoreRef
from quantlab.features.transformers import (
    ClosePriceTransformer,
    LogReturnTransformer,
    SimpleReturnTransformer,
    VolumeChangeTransformer,
    VolumeSMATransformer,
)

__all__ = [
    "ATRIndicator",
    "ClosePriceTransformer",
    "EMACloseIndicator",
    "FeatureFrame",
    "FeaturePipeline",
    "FeaturePoint",
    "FeatureSeries",
    "FeatureStore",
    "FeatureStoreRef",
    "FeatureTransformer",
    "Indicator",
    "LogReturnTransformer",
    "RSIWilderIndicator",
    "SMACloseIndicator",
    "SimpleReturnTransformer",
    "VolumeChangeTransformer",
    "VolumeSMATransformer",
    "build_pipeline",
]
