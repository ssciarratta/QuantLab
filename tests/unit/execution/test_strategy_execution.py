"""Tests Strategy Execution MVP (Fase A–O)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.execution.strategy_execution import (
    MAX_ACTIVE_STRATEGIES,
    ExecutionDestination,
    ExecutionSessionState,
    StrategyExecutionService,
    default_store,
)
from quantlab.execution.strategy_execution.registry import get_registry
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.execution_api import (
    handle_get_execution_strategies,
    handle_post_execution_promotion_open_session,
    handle_post_execution_promotion_preflight,
    handle_post_execution_promotion_validate,
    handle_post_execution_promotions,
    handle_post_execution_run,
    handle_post_execution_session_start_paper,
    handle_post_execution_session_stop,
)
from quantlab.workbench.session import WorkbenchSession


def test_registry_buy_once_spot_certified() -> None:
    caps = get_registry().get("buy_once")
    assert caps.paper_supported is True
    assert caps.spot_testnet_supported is True
    assert caps.futures_testnet_supported is False
    assert caps.certification_status.value == "SPOT_TESTNET_READY"


def test_manifest_and_validate(tmp_path: Path) -> None:
    svc = StrategyExecutionService(default_store(str(tmp_path / "exec")))
    manifest = svc.create_promotion(
        {
            "source_module": "manual",
            "strategy_id": "buy_once",
            "symbol": "BTCUSDT",
            "execution_destination": ExecutionDestination.PAPER.value,
        }
    )
    assert manifest.promotion_id
    assert manifest.configuration_hash
    val = svc.validate_promotion(manifest.promotion_id)
    assert val["ok"] is True


def test_preflight_never_enables_remote_orders(tmp_path: Path) -> None:
    svc = StrategyExecutionService(default_store(str(tmp_path / "exec")))
    manifest = svc.create_promotion(
        {
            "source_module": "manual",
            "strategy_id": "buy_once",
            "symbol": "ETHUSDT",
            "execution_destination": ExecutionDestination.PAPER.value,
        }
    )
    pf = svc.preflight(manifest.promotion_id, unlocked=False)
    assert pf.ready_for_spot_testnet_order is False
    assert pf.ready_for_futures_testnet_order is False
    assert pf.to_dict()["remote_orders_enabled"] is False
    assert LIVE_BLOCKED is True


def test_max_active_blocks_running_session(tmp_path: Path) -> None:
    store = default_store(str(tmp_path / "exec"))
    svc = StrategyExecutionService(store)
    m1 = svc.create_promotion(
        {
            "source_module": "manual",
            "strategy_id": "buy_once",
            "symbol": "BTCUSDT",
            "execution_destination": ExecutionDestination.PAPER.value,
        }
    )
    rec = svc.open_session(m1.promotion_id)
    rec.state = ExecutionSessionState.RUNNING
    store.save_session(rec)
    m2 = svc.create_promotion(
        {
            "source_module": "manual",
            "strategy_id": "buy_once",
            "symbol": "ETHUSDT",
            "execution_destination": ExecutionDestination.PAPER.value,
        }
    )
    with pytest.raises(ValidationError, match=str(MAX_ACTIVE_STRATEGIES)):
        svc.open_session(m2.promotion_id)


def test_scanner_promotion_helper(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "exec-api")
    state = WorkbenchState(session=session)
    res = handle_post_execution_promotions(
        state,
        {
            "source_module": "alpha_scanner",
            "scan_id": "scan-abc",
            "strategy_id": "buy_once",
            "underlying": "BTC",
            "interval": "1h",
            "score": 0.42,
        },
    )
    assert res["ok"] is True
    pid = res["promotion"]["promotion_id"]
    val = handle_post_execution_promotion_validate(state, pid)
    assert val["ok"] is True
    pf = handle_post_execution_promotion_preflight(state, pid)
    assert pf["preflight"]["ready_for_spot_testnet_order"] is False
    opened = handle_post_execution_promotion_open_session(state, pid)
    assert opened["session"]["state"] == "DRAFT"


def test_list_strategies_api(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "exec-list")
    state = WorkbenchState(session=session)
    res = handle_get_execution_strategies(state)
    assert res["ok"] is True
    assert res["production_blocked"] is True
    ids = {s["strategy_id"] for s in res["strategies"]}
    assert "buy_once" in ids
    buy = next(s for s in res["strategies"] if s["strategy_id"] == "buy_once")
    assert buy["paper_run_certified"] is True
    adapt = next(s for s in res["strategies"] if s["strategy_id"] == "adaptive_mm")
    assert adapt["paper_run_certified"] is True


def test_start_paper_buy_once(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "exec-paper")
    state = WorkbenchState(session=session)
    promo = handle_post_execution_promotions(
        state,
        {
            "source_module": "manual",
            "strategy_id": "buy_once",
            "symbol": "BTCUSDT",
            "execution_destination": "PAPER",
        },
    )
    pid = promo["promotion"]["promotion_id"]
    handle_post_execution_promotion_validate(state, pid)
    handle_post_execution_promotion_preflight(state, pid)
    opened = handle_post_execution_promotion_open_session(state, pid)
    sid = opened["session"]["session_id"]
    started = handle_post_execution_session_start_paper(state, sid, {"max_steps": 3})
    assert started["ok"] is True
    assert started["session"]["state"] == "RUNNING"
    assert started["session"]["paper_session_running"] is True
    assert started["paper_status"]["running"] is True
    stopped = handle_post_execution_session_stop(state, sid)
    assert stopped["ok"] is True
    assert stopped["closure_summary"]["outcome"] == "stopped"
    assert isinstance(stopped["closure_summary"]["done"], list)
    assert isinstance(stopped["closure_summary"]["not_done"], list)


def test_execution_run_one_click_buy_once(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "exec-run")
    state = WorkbenchState(session=session)
    res = handle_post_execution_run(
        state,
        {
            "source_module": "manual",
            "strategy_id": "buy_once",
            "symbol": "BTCUSDT",
            "execution_destination": "PAPER",
            "max_steps": 4,
            "interval_ms": 100,
        },
    )
    assert res["ok"] is True
    assert res["paper_started"] is True
    assert res["session_id"]
    assert res["live"]["live_summary"]["paper_running"] is True
    handle_post_execution_session_stop(state, res["session_id"])


def test_execution_run_adaptive_mm_starts_paper(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "exec-adapt-run")
    state = WorkbenchState(session=session)
    res = handle_post_execution_run(
        state,
        {
            "source_module": "manual",
            "strategy_id": "adaptive_mm",
            "symbol": "BTCUSDT",
            "execution_destination": "PAPER",
            "max_steps": 3,
            "interval_ms": 100,
        },
    )
    assert res["ok"] is True
    assert res["paper_started"] is True
    assert res["session_id"]
    handle_post_execution_session_stop(state, res["session_id"])


def test_start_paper_adaptive_mm(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "exec-adapt")
    state = WorkbenchState(session=session)
    promo = handle_post_execution_promotions(
        state,
        {
            "source_module": "manual",
            "strategy_id": "adaptive_mm",
            "symbol": "BTCUSDT",
            "execution_destination": "PAPER",
        },
    )
    pid = promo["promotion"]["promotion_id"]
    opened = handle_post_execution_promotion_open_session(state, pid)
    sid = opened["session"]["session_id"]
    started = handle_post_execution_session_start_paper(
        state, sid, {"max_steps": 5, "interval_ms": 100}
    )
    assert started["ok"] is True
    assert started["session"]["paper_session_running"] is True
    handle_post_execution_session_stop(state, sid)
