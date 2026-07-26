"""Tests Report Viewer + Metrics History (F29)."""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import (
    WorkbenchState,
    handle_get_lab_report,
    handle_get_lab_reports,
    handle_post_lab_backtest,
)
from quantlab.workbench.lab_services import run_lab_backtest
from quantlab.workbench.reports import (
    get_lab_report,
    list_lab_reports,
    persist_backtest_report,
    validate_report_id,
)
from quantlab.workbench.session import WorkbenchSession


def test_live_blocked_still_true() -> None:
    assert LIVE_BLOCKED is True


def test_validate_report_id_rejects_traversal() -> None:
    with pytest.raises(ValidationError, match="report_id"):
        validate_report_id("../evil")
    with pytest.raises(ValidationError, match="report_id"):
        validate_report_id("a/b")
    assert validate_report_id("wb-lab-backtest-20260726T010203000Z")


def test_session_reports_dir(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "rep1")
    assert session.reports_dir == session.root / "reports"
    assert session.reports_dir.is_dir()
    assert "reports" in session.to_dict()


def test_persist_list_get_roundtrip(tmp_path: Path) -> None:
    reports_root = tmp_path / "reports"
    result = run_lab_backtest(
        strategy_id="momentum",
        n_bars=12,
        experiment_id="wb-f29-rt",
        reports_dir=reports_root,
    )
    assert result["ok"] is True
    assert result["live_blocked"] is True
    assert "report_id" in result
    rid = result["report_id"]
    assert isinstance(rid, str)
    summary_path = Path(str(result["report_path"]))
    assert summary_path.is_file()

    listed = list_lab_reports(reports_root)
    assert listed["ok"] is True
    assert listed["count"] >= 1
    assert listed["reports"][0]["report_id"] == rid

    got = get_lab_report(reports_root, rid)
    assert got["ok"] is True
    assert got["report_id"] == rid
    assert got["report"]["metrics_result"]["experiment_id"] == "wb-f29-rt"
    assert got["has_html"] is True
    assert got["html"] is not None
    assert "QuantLab" in got["html"]


def test_persist_without_reports_dir_no_side_effect(tmp_path: Path) -> None:
    result = run_lab_backtest(strategy_id="buy_once", n_bars=8, experiment_id="wb-no-persist")
    assert "report_id" not in result
    assert not (tmp_path / "reports").exists()


def test_api_handlers_backtest_persists(tmp_path: Path) -> None:
    session = WorkbenchSession.create_or_load(tmp_path, "api-rep")
    state = WorkbenchState(session=session)
    state.ensure_session()
    body = handle_post_lab_backtest(
        state,
        {"strategy_id": "momentum", "n_bars": 10, "experiment_id": "wb-api-bt"},
    )
    assert body["ok"] is True
    assert body["report_id"]
    listed = handle_get_lab_reports(state)
    assert listed["count"] >= 1
    detail = handle_get_lab_report(state, body["report_id"])
    assert detail["has_html"] is True
    assert detail["live_blocked"] is True


def test_api_get_report_404(tmp_path: Path) -> None:
    from quantlab.workbench.api import ApiError

    session = WorkbenchSession.create_or_load(tmp_path, "missing")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError) as exc:
        handle_get_lab_report(state, "does-not-exist-yet-0001")
    assert exc.value.status == 404


def test_api_get_report_bad_id(tmp_path: Path) -> None:
    from quantlab.workbench.api import ApiError

    session = WorkbenchSession.create_or_load(tmp_path, "badid")
    state = WorkbenchState(session=session)
    state.ensure_session()
    with pytest.raises(ApiError) as exc:
        handle_get_lab_report(state, "../x")
    assert exc.value.status == 400


def _addr(server: ThreadingHTTPServer) -> tuple[str, int]:
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    return host, port


def _get(server: ThreadingHTTPServer, path: str) -> tuple[int, dict[str, Any]]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return resp.status, body


def _post(
    server: ThreadingHTTPServer, path: str, payload: dict[str, Any] | None = None
) -> tuple[int, dict[str, Any]]:
    host, port = _addr(server)
    conn = http.client.HTTPConnection(host, port, timeout=60)
    raw = json.dumps(payload or {}).encode("utf-8")
    conn.request(
        "POST",
        path,
        body=raw,
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return resp.status, body


def test_http_reports_flow(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, empty = _get(server, "/api/lab/reports")
    assert status == 200
    assert empty["ok"] is True
    assert empty["live_blocked"] is True

    status, bt = _post(
        server,
        "/api/lab/backtest",
        {"strategy_id": "momentum", "n_bars": 12, "experiment_id": "wb-http-rep"},
    )
    assert status == 200
    assert bt["report_id"]
    rid = bt["report_id"]

    status, listed = _get(server, "/api/lab/reports")
    assert status == 200
    assert listed["count"] >= 1
    ids = {r["report_id"] for r in listed["reports"]}
    assert rid in ids

    status, detail = _get(server, f"/api/lab/reports/{rid}")
    assert status == 200
    assert detail["report_id"] == rid
    assert detail["has_html"] is True
    assert "QuantLab" in (detail["html"] or "")

    status, missing = _get(server, "/api/lab/reports/no-such-report-zzzz")
    assert status == 404
    assert "error" in missing


def test_capabilities_include_reports(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/capabilities")
    assert status == 200
    ids = {f["id"] for f in body["features"]}
    assert "reports" in ids


def test_persist_backtest_report_direct(tmp_path: Path) -> None:
    """Persist vía API de bajo nivel (MetricsResult real desde backtest)."""
    # Corre backtest sin persistir, luego persiste con metrics del resultado interno.
    from datetime import UTC, datetime
    from decimal import Decimal

    from quantlab.core.types.results import EquityPoint, MetricsResult, SimulationResult

    metrics = MetricsResult(
        experiment_id="wb-direct",
        metrics={"sharpe": 1.2, "max_drawdown": 0.05, "n_trades": 2},
        computed_at=datetime(2024, 6, 1, tzinfo=UTC),
        metrics_version="test-1",
    )
    sim = SimulationResult(
        experiment_id="wb-direct",
        equity_curve=(
            EquityPoint(timestamp=datetime(2024, 6, 1, 0, 0, tzinfo=UTC), equity=Decimal("100")),
            EquityPoint(timestamp=datetime(2024, 6, 1, 0, 1, tzinfo=UTC), equity=Decimal("101")),
        ),
        fills=(),
        orders=(),
        portfolio_snapshots=(),
        events_log=(),
    )
    summary = {
        "ok": True,
        "kind": "backtest",
        "strategy_id": "momentum",
        "experiment_id": "wb-direct",
        "final_equity": "101",
        "live_routing": False,
        "live_blocked": True,
    }
    meta = persist_backtest_report(
        tmp_path / "reports",
        metrics=metrics,
        simulation=sim,
        summary=summary,
        report_id="wb-direct-manual-001",
    )
    assert meta["report_id"] == "wb-direct-manual-001"
    assert meta["has_html"] is True
    got = get_lab_report(tmp_path / "reports", "wb-direct-manual-001")
    assert got["report"]["metrics_result"]["metrics"]["sharpe"] == 1.2
