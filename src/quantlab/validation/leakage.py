"""Detección de look-ahead / leakage temporal (Fase 10)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from quantlab.core.types.market import Bar
from quantlab.validation.splits import assert_no_future_overlap


@dataclass(frozen=True, slots=True)
class LeakageReport:
    ok: bool
    issues: tuple[str, ...]


def check_temporal_leakage(
    train: Sequence[Bar],
    test: Sequence[Bar],
) -> LeakageReport:
    issues: list[str] = []
    try:
        assert_no_future_overlap(train, test)
    except Exception as exc:  # noqa: BLE001 — reportamos como issue
        issues.append(str(exc))
    # IDs de instrumento mixtos
    if train and test and train[0].instrument_id != test[0].instrument_id:
        issues.append("instrument_id distinto entre train/test")
    return LeakageReport(ok=not issues, issues=tuple(issues))
