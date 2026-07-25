"""Scientific Validation (Fase 10)."""

from quantlab.validation.leakage import LeakageReport, check_temporal_leakage
from quantlab.validation.multiple_testing import (
    MultipleTestingResult,
    adjust_pvalues,
    benjamini_hochberg,
    bonferroni,
    filter_significant,
    holm_bonferroni,
)
from quantlab.validation.splits import SplitResult, WalkForwardSplit, train_val_oos_split

__all__ = [
    "LeakageReport",
    "MultipleTestingResult",
    "SplitResult",
    "WalkForwardSplit",
    "adjust_pvalues",
    "benjamini_hochberg",
    "bonferroni",
    "check_temporal_leakage",
    "filter_significant",
    "holm_bonferroni",
    "train_val_oos_split",
]
