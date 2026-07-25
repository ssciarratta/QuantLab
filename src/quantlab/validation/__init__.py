"""Scientific Validation (Fase 10)."""

from quantlab.validation.leakage import LeakageReport, check_temporal_leakage
from quantlab.validation.splits import SplitResult, WalkForwardSplit, train_val_oos_split

__all__ = [
    "LeakageReport",
    "SplitResult",
    "WalkForwardSplit",
    "check_temporal_leakage",
    "train_val_oos_split",
]
