"""Smoke del vertical slice Fase 4."""

from __future__ import annotations

from quantlab.vertical_slice.fase4 import run_fase4_slice


def test_fase4_slice_smoke() -> None:
    result = run_fase4_slice()
    assert result.simulation.equity_curve
    assert result.metrics.metrics_version
    assert "sharpe" in result.metrics.metrics
    assert result.scanner.selected or result.scanner.scores is not None
