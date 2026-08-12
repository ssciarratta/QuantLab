"""Detectores Alpha Scanner (individual, par, grupo)."""

from quantlab.research.alpha.detectors.base import (
    AlphaDetector,
    DetectorContext,
    DetectorRunConfig,
)
from quantlab.research.alpha.detectors.registry import (
    DetectorRegistry,
    global_registry,
    register_detector,
)

__all__ = [
    "AlphaDetector",
    "DetectorContext",
    "DetectorRunConfig",
    "DetectorRegistry",
    "global_registry",
    "register_detector",
]
