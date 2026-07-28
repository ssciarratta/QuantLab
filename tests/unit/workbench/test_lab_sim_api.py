"""Smoke tests (sin red) para handlers /api/lab/sim/*."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_lab_sim_fees,
    handle_get_lab_sim_period,
    handle_post_lab_sim_compare,
    handle_post_lab_sim_sizing,
)
from quantlab.workbench.session import WorkbenchSession


def test_handle_get_lab_sim_fees(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-fees")
    state = WorkbenchState(session=session)
    out = handle_get_lab_sim_fees(state)
    assert out["ok"] is True
    assert out["kind"] == "sim_fees"
    assert out["live_blocked"] is True
    assert out["live_routing"] is False
    assert out["research_safe"] is True
    schedules = out["schedules"]
    assert isinstance(schedules, list)
    assert len(schedules) == 8
    venues = {row["venue"] for row in schedules}
    assert venues == {"binance", "okx", "bybit", "hyperliquid"}
    sample = schedules[0]
    assert "maker_bps" in sample
    assert "taker_bps" in sample


def test_handle_get_lab_sim_period_defaults(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-period")
    state = WorkbenchState(session=session)
    out = handle_get_lab_sim_period(state, "")
    assert out["ok"] is True
    assert out["period_days"] == "30"
    assert out["interval"] == "1h"
    assert out["n_bars"] == 720
    assert out["live_blocked"] is LIVE_BLOCKED
    assert out["live_routing"] is False
    assert "binance_intervals" in out


def test_handle_get_lab_sim_period_query(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-period-q")
    state = WorkbenchState(session=session)
    out = handle_get_lab_sim_period(state, "period_days=7&interval=4h")
    assert out["period_days"] == "7"
    assert out["interval"] == "4h"
    assert out["n_bars"] == 42


def test_handle_get_lab_sim_period_invalid_interval(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-period-bad")
    state = WorkbenchState(session=session)
    with pytest.raises(ApiError) as exc:
        handle_get_lab_sim_period(state, "interval=2x")
    assert exc.value.status == 400
    assert "interval inválido" in exc.value.message


def test_handle_post_lab_sim_sizing_ok(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-sizing")
    state = WorkbenchState(session=session)
    out = handle_post_lab_sim_sizing(
        state,
        {
            "initial_capital": "10000",
            "per_trade_usd": "1000",
            "leverage": "5",
            "market_type": "futures",
        },
    )
    assert out["ok"] is True
    assert out["kind"] == "sim_sizing"
    assert out["margin"] == "1000"
    assert out["notional"] == "5000"
    assert out["live_blocked"] is True
    assert out["live_routing"] is False


def test_handle_post_lab_sim_sizing_invalid_body(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-sizing-bad")
    state = WorkbenchState(session=session)
    with pytest.raises(ApiError) as exc:
        handle_post_lab_sim_sizing(state, "not-a-dict")  # type: ignore[arg-type]
    assert exc.value.status == 400
    assert "body JSON objeto requerido" in exc.value.message


def test_handle_post_lab_sim_sizing_margin_exceeds_capital(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-sizing-val")
    state = WorkbenchState(session=session)
    out = handle_post_lab_sim_sizing(
        state,
        {
            "initial_capital": "100",
            "per_trade_usd": "5000",
            "leverage": "10",
            "market_type": "futures",
        },
    )
    assert out["ok"] is False
    assert any("excede capital" in e for e in out["errors"])


def test_handle_post_lab_sim_sizing_invalid_market_type(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-sizing-mt")
    state = WorkbenchState(session=session)
    with pytest.raises(ApiError) as exc:
        handle_post_lab_sim_sizing(
            state,
            {
                "initial_capital": "10000",
                "per_trade_usd": "1000",
                "leverage": "1",
                "market_type": "options",
            },
        )
    assert exc.value.status == 400
    assert "market_type inválido" in exc.value.message


def test_handle_post_lab_sim_compare_mocked(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-compare")
    state = WorkbenchState(session=session)
    state.ensure_session()
    fake_result = {
        "ok": True,
        "rows": [
            {
                "venue": "binance",
                "market_type": "futures",
                "underlying": "BTC",
                "instrument_id": "BTCUSDT",
                "leverage": "1",
                "strategy_id": "momentum",
                "ok": True,
            }
        ],
        "common": {
            "strategy_id": "momentum",
            "market_type": "futures",
            "interval": "1h",
            "kline_limit": 24,
            "initial_capital": "100000",
            "per_trade_usd": "1000",
            "annual_bench_rate": "0.05",
            "simulate_liquidation": True,
            "apply_funding": True,
            "extra_costs": [],
            "benchmarks_by_key": {},
        },
        "live_blocked": True,
    }
    body = {
        "venues": ["binance"],
        "underlyings": ["BTC"],
        "strategy_id": "momentum",
        "market_type": "futures",
        "interval": "1h",
        "kline_limit": 24,
    }
    with patch(
        "quantlab.research.sim.compare.run_sim_compare",
        return_value=fake_result,
    ) as mock_run:
        out = handle_post_lab_sim_compare(state, body)
    mock_run.assert_called_once_with(body)
    assert out["ok"] is True
    assert out["session_id"] == state.session.session_id
    assert state.last_lab_result is out
    assert len(out["rows"]) == 1


def test_handle_post_lab_sim_compare_validation_error(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path / "sessions", "sim-compare-bad")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError) as exc:
        handle_post_lab_sim_compare(state, {})
    assert exc.value.status == 400
    assert "venues+underlyings" in exc.value.message or "pairs" in exc.value.message


def test_compare_fee_overrides_wire_into_fills_note() -> None:
    """maker/taker bps del request alimentan MakerTakerFeeModel (taker en 5A)."""
    import inspect

    from quantlab.research.sim import compare as compare_mod

    src = inspect.getsource(compare_mod.run_sim_compare)
    assert 'request.get("maker_bps")' in src
    assert "fee_model_from_schedule" in src
    assert "fee_model=" in src
    assert "fee_fills_note" in src
