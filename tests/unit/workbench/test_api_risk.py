"""Tests GET /api/risk (F25 Ops Desk panel Riesgo)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from quantlab.workbench.api import WorkbenchState, handle_get_risk
from quantlab.workbench.risk import PaperRiskLimits
from quantlab.workbench.session import WorkbenchSession


def test_handle_get_risk_shape(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(
        tmp_path,
        "risksess01",
        initial_cash=Decimal("25000"),
    )
    state = WorkbenchState(
        session=session,
        initial_cash=Decimal("25000"),
        slippage_bps=Decimal("7"),
        risk=PaperRiskLimits(
            max_qty=Decimal("10"),
            max_notional=Decimal("1000"),
            allowed_symbols=frozenset({"AAA"}),
        ),
    )
    state.ensure_session()
    out = handle_get_risk(state)
    assert out["ok"] is True
    assert out["live_blocked"] is True
    assert out["slippage_bps"] == "7"
    assert out["session_id"] == "risksess01"
    assert out["limits"]["max_qty"] == "10"
    assert out["limits"]["max_notional"] == "1000"
    assert out["limits"]["allowed_symbols"] == ["AAA"]
    assert "risksess01" in out["session_root"]


def test_handle_get_risk_allowed_symbols_none(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "risksess02")
    state = WorkbenchState(session=session)
    state.ensure_session()
    out = handle_get_risk(state)
    assert out["limits"]["allowed_symbols"] is None
