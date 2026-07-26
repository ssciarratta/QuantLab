#!/usr/bin/env python3
"""Smoke INTERNAL Zero-Trust — invariantes LIVE + imports workbench/brokers.

Uso:
  uv run python scripts/internal_audit_smoke.py

Exit 0 = all PASS; exit 1 = algún FAIL.
"""

from __future__ import annotations

import sys
from collections.abc import Callable


def _check(name: str, fn: Callable[[], None]) -> bool:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — smoke reporta cualquier fallo
        print(f"FAIL  {name}: {exc}")
        return False
    print(f"PASS  {name}")
    return True


def check_live_blocked() -> None:
    from quantlab.execution.live_gate import LIVE_BLOCKED

    assert LIVE_BLOCKED is True, f"LIVE_BLOCKED={LIVE_BLOCKED!r} (expected True)"


def check_live_gate_raises() -> None:
    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import assert_live_routing_blocked

    try:
        assert_live_routing_blocked()
    except ValidationError:
        return
    raise AssertionError("assert_live_routing_blocked should raise when LIVE_BLOCKED")


def check_brokers_imports() -> None:
    from quantlab.brokers.mode import REAL_ALIAS, ModeGuard, OperatingMode
    from quantlab.brokers.registry import get_default_registry

    assert REAL_ALIAS is OperatingMode.PAPER
    assert OperatingMode.LIVE in OperatingMode
    _ = ModeGuard
    reg = get_default_registry()
    venues = set(reg.list_venues())
    assert {"a3", "binance", "paper", "generic_csv", "generic_rest"}.issubset(venues), venues


def check_workbench_imports() -> None:
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.launch import main as _launch_main  # noqa: F401
    from quantlab.workbench.server import create_server

    state = WorkbenchState()
    assert state.mode.value in {"tester", "paper"}
    _ = create_server


def check_chat_safe() -> None:
    from quantlab.core.exceptions import ValidationError
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.chat.providers import FakeProvider, build_default_provider
    from quantlab.workbench.chat.tools import ALLOWED_TOOLS, FORBIDDEN_TOOLS, ToolRegistry

    provider = build_default_provider()
    assert isinstance(provider, FakeProvider), type(provider).__name__
    assert "submit_order" not in ALLOWED_TOOLS
    assert "place_order" in FORBIDDEN_TOOLS
    assert "set_live" in FORBIDDEN_TOOLS
    assert ALLOWED_TOOLS.isdisjoint(FORBIDDEN_TOOLS)
    for name in ("get_session_summary", "list_reports", "list_strategies"):
        assert name in ALLOWED_TOOLS

    reg = ToolRegistry(WorkbenchState())
    for bad in ("submit_order", "place_order", "set_live", "flip_live_blocked"):
        try:
            reg.call(bad)
        except ValidationError:
            continue
        raise AssertionError(f"expected reject for {bad}")


def check_f47_chat_context() -> None:
    """F47: chat context tools + FakeProvider ES + LIVE_BLOCKED."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.chat.providers import FakeProvider
    from quantlab.workbench.chat.tools import ALLOWED_TOOLS, FORBIDDEN_TOOLS, ToolRegistry
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.strategy_catalog import CANONICAL_STRATEGY_IDS

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"
    assert "get_session_summary" in ALLOWED_TOOLS
    assert "list_reports" in ALLOWED_TOOLS
    assert "list_strategies" in ALLOWED_TOOLS
    assert ALLOWED_TOOLS.isdisjoint(FORBIDDEN_TOOLS)

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f47-"))
    session = WorkbenchSession.create_or_load(root, "smoke47")
    state = WorkbenchState(session=session)
    state.ensure_session()
    reg = ToolRegistry(state)

    summary = reg.call("get_session_summary", {"limit": 5})
    assert summary["ok"] is True
    assert summary["mode"] in {"tester", "paper"}
    assert "book_equity" in summary
    assert summary["positions_count"] >= 0
    assert summary["live_blocked"] is True

    reports = reg.call("list_reports")
    assert reports["ok"] is True
    assert reports["kind"] == "reports"

    strategies = reg.call("list_strategies")
    assert strategies["ok"] is True
    assert strategies["count"] == len(CANONICAL_STRATEGY_IDS)

    for bad in ("submit_order", "place_order", "set_live", "paper_submit"):
        try:
            reg.call(bad)
            raise AssertionError(f"expected reject for {bad}")
        except Exception as exc:  # noqa: BLE001
            assert "rechazada" in str(exc).lower()

    fake = FakeProvider()
    assert "get_session_summary" in fake.complete("¿cómo estoy?", reg).tools_used
    assert "get_session_summary" in fake.complete("resumen sesión", reg).tools_used
    assert "list_reports" in fake.complete("qué reportes hay", reg).tools_used
    assert "list_strategies" in fake.complete("estrategias", reg).tools_used


def check_health_dict() -> None:
    from quantlab import __version__
    from quantlab.infra.health import run_health_checks

    report = run_health_checks().to_dict()
    assert report.get("ok") is True
    assert report.get("live_blocked") is True
    assert report.get("version") == __version__


def check_about_version_matches() -> None:
    """F49: About / health version ≡ quantlab.__version__."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.infra.health import run_health_checks
    from quantlab.workbench.about import PHASES_SUMMARY, build_about_payload
    from quantlab.workbench.api import WorkbenchState, handle_get_about
    from quantlab.workbench.session import WorkbenchSession

    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"

    about = build_about_payload()
    assert about["version"] == __version__
    assert about["phases_summary"] == PHASES_SUMMARY
    assert about["live_blocked"] is True

    health = run_health_checks().to_dict()
    assert health.get("version") == __version__

    root = Path("/tmp/quantlab-smoke-f49-about-ver")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke49")
    state = WorkbenchState(session=session)
    state.ensure_session()
    body = handle_get_about(state)
    assert body["version"] == __version__
    assert body["version"] == about["version"]


def check_paper_book_session() -> None:
    """F23: PaperBook fail-closed + session_id anti-traversal."""
    from decimal import Decimal

    from quantlab.brokers.paper.book import PaperBook
    from quantlab.core.exceptions import ValidationError
    from quantlab.workbench.risk import PaperRiskLimits
    from quantlab.workbench.session import WorkbenchSession, validate_session_id

    book = PaperBook(initial_cash=Decimal("1000"))
    assert book.cash == Decimal("1000")
    assert book.allow_short is False
    try:
        PaperBook(initial_cash=Decimal("100"), cash=Decimal("-1"))
    except ValidationError:
        pass
    else:
        raise AssertionError("negative cash should raise")

    validate_session_id("s1")
    for bad in ("../escape", "a/b", "..", ""):
        try:
            validate_session_id(bad)
        except ValidationError:
            continue
        raise AssertionError(f"expected reject session_id {bad!r}")

    _ = PaperRiskLimits
    _ = WorkbenchSession


def check_f23_book_import() -> None:
    """F23: import surface PaperBook / PaperBroker / journal."""
    from quantlab.brokers.paper import PaperBook, PaperBroker, PaperFillJournal
    from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH

    assert DEFAULT_INITIAL_CASH > 0
    _ = PaperBook, PaperBroker, PaperFillJournal


def check_f24_plugins() -> None:
    """F24: entry-point loader + generics en registry."""
    from quantlab.brokers.plugins import load_entry_point_brokers
    from quantlab.brokers.registry import BrokerRegistry, get_default_registry

    reg = get_default_registry()
    assert "generic_csv" in reg.list_venues()
    assert "generic_rest" in reg.list_venues()
    # loader no crashea sobre registry vacío
    empty = BrokerRegistry()
    load_entry_point_brokers(empty)


def check_f25_launch_parser() -> None:
    """F25: --allow-non-loopback en parser + is_loopback_host."""
    from quantlab.workbench.launch import build_parser, is_loopback_host

    parser = build_parser()
    ns = parser.parse_args(["--allow-non-loopback", "--host", "0.0.0.0"])
    assert ns.allow_non_loopback is True
    assert is_loopback_host("127.0.0.1") is True
    assert is_loopback_host("0.0.0.0") is False
    # flag presente en help
    help_txt = parser.format_help()
    assert "--allow-non-loopback" in help_txt
    assert "--slippage-bps" in help_txt


def check_f25_ops_desk_invariants() -> None:
    """F25: experiment_id charset + slip adverso + risk payload."""
    from decimal import Decimal

    from quantlab.brokers.paper.broker import apply_paper_slippage
    from quantlab.core.exceptions import ValidationError
    from quantlab.workbench.api import WorkbenchState, handle_get_risk
    from quantlab.workbench.lab_services import validate_experiment_id

    assert validate_experiment_id("wb-ok") == "wb-ok"
    try:
        validate_experiment_id("../evil")
    except ValidationError:
        pass
    else:
        raise AssertionError("expected reject experiment_id traversal")

    assert apply_paper_slippage(Decimal("100"), "BUY", Decimal("100")) == Decimal("101")
    assert apply_paper_slippage(Decimal("100"), "SELL", Decimal("100")) == Decimal("99")

    state = WorkbenchState(slippage_bps=Decimal("3"))
    state.ensure_session()
    risk = handle_get_risk(state)
    assert risk.get("ok") is True
    assert risk.get("live_blocked") is True
    assert risk.get("slippage_bps") == "3"
    assert "max_qty" in risk.get("limits", {})


def check_f26_paper_session() -> None:
    """F26: PaperSessionRunner import + LIVE_BLOCKED + status shape."""
    from datetime import UTC, datetime
    from decimal import Decimal

    from quantlab.brokers.paper.book import PaperBook
    from quantlab.brokers.paper.broker import PaperBroker
    from quantlab.brokers.types import (
        BrokerAccount,
        BrokerAck,
        BrokerInstrument,
        BrokerPosition,
        BrokerSnapshot,
    )
    from quantlab.core.types.orders import OrderIntent
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.paper_session import (
        PaperSessionConfig,
        PaperSessionRunner,
        build_session_strategy,
    )
    from quantlab.workbench.risk import PaperRiskLimits

    assert LIVE_BLOCKED is True
    _ = build_session_strategy("dummy")
    _ = PaperSessionConfig(strategy_id="buy_once", symbol="X", max_steps=2)

    class _Md:
        @property
        def venue_id(self) -> str:
            return "smoke-md"

        def connect(self) -> dict[str, object]:
            return {}

        def close(self) -> dict[str, object]:
            return {}

        def health(self) -> dict[str, object]:
            return {}

        def list_instruments(self) -> list[BrokerInstrument]:
            return []

        def get_snapshot(self, symbol: str) -> BrokerSnapshot:
            return BrokerSnapshot(
                symbol=symbol,
                bid=Decimal("9"),
                ask=Decimal("11"),
                last=Decimal("10"),
                ts=datetime(2024, 1, 1, tzinfo=UTC),
            )

        def get_account(self) -> BrokerAccount:
            return BrokerAccount(cash=Decimal("1"), currency="USD")

        def get_positions(self) -> list[BrokerPosition]:
            return []

        def submit(self, intent: OrderIntent) -> BrokerAck:
            raise AssertionError("no venue submit")

        def cancel(self, order_id: str) -> BrokerAck:
            raise AssertionError("no venue cancel")

    book = PaperBook()
    broker = PaperBroker(_Md(), book=book)
    runner = PaperSessionRunner(broker, PaperRiskLimits(), book)
    st = runner.status()
    assert st["running"] is False
    assert st["live_blocked"] is True

    # Fail-closed: MD/venue stub no es PaperBroker
    try:
        PaperSessionRunner(_Md(), PaperRiskLimits(), book)  # type: ignore[arg-type]
    except Exception as exc:
        assert "PaperBroker" in str(exc)
    else:
        raise AssertionError("expected reject non-PaperBroker")

    runner.start(PaperSessionConfig(strategy_id="buy_once", symbol="X", max_steps=2))
    summary = runner.step()
    assert summary.get("live_routing") is False
    assert summary.get("live_blocked") is True
    runner.stop()


def check_f27_strategy_catalog() -> None:
    """F27: catálogo + MM wire + lab strategies sin LIVE."""
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.lab_services import lab_strategies, run_lab_backtest
    from quantlab.workbench.strategy_catalog import (
        CANONICAL_STRATEGY_IDS,
        build_strategy,
        list_strategy_catalog,
        normalize_strategy_id,
    )

    assert LIVE_BLOCKED is True
    assert "inventory_mm" in CANONICAL_STRATEGY_IDS
    assert "avellaneda_stoikov" in CANONICAL_STRATEGY_IDS
    assert normalize_strategy_id("as") == "avellaneda_stoikov"
    cats = list_strategy_catalog()
    assert len(cats) == len(CANONICAL_STRATEGY_IDS)
    for sid in CANONICAL_STRATEGY_IDS:
        build_strategy(sid).reset()
        result = run_lab_backtest(strategy_id=sid, n_bars=8)
        assert result["ok"] is True
        assert result["live_blocked"] is True
        assert result["live_routing"] is False
    body = lab_strategies()
    assert body["ok"] is True
    assert "inventory_mm" in body["ids"]


def check_f28_layout_journal() -> None:
    """F28: layout save/load + API handlers + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import WorkbenchState, handle_get_layout, handle_put_layout
    from quantlab.workbench.layout import load_layout, save_layout
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = Path("/tmp/quantlab-smoke-f28-layout")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke28")
    path = session.layout_path
    saved = save_layout(
        path,
        {"version": 1, "windows": {"health": {"x": 1, "y": 2, "w": 300, "h": 200}}},
    )
    assert load_layout(path) == saved
    state = WorkbenchState(session=session)
    state.ensure_session()
    put = handle_put_layout(
        state,
        {"layout": {"version": 1, "windows": {"journal": {"x": 5, "y": 6, "w": 400, "h": 300}}}},
    )
    assert put["ok"] is True
    assert put["live_blocked"] is True
    got = handle_get_layout(state)
    assert got["layout"]["windows"]["journal"]["w"] == 400


def check_f29_reports() -> None:
    """F29: persist report tras backtest + list/get + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_report,
        handle_get_lab_reports,
        handle_post_lab_backtest,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = Path("/tmp/quantlab-smoke-f29-reports")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke29")
    state = WorkbenchState(session=session)
    state.ensure_session()
    body = handle_post_lab_backtest(
        state,
        {"strategy_id": "momentum", "n_bars": 10, "experiment_id": "wb-smoke29"},
    )
    assert body["ok"] is True
    assert body["live_blocked"] is True
    assert body["report_id"]
    listed = handle_get_lab_reports(state)
    assert listed["ok"] is True
    assert listed["count"] >= 1
    detail = handle_get_lab_report(state, body["report_id"])
    assert detail["has_html"] is True
    assert detail["live_routing"] is False


def check_f30_universe_catalog() -> None:
    """F30: watchlist + universe + catalog empty-ok + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_catalog,
        handle_get_universe,
        handle_get_watchlist,
        handle_put_watchlist,
    )
    from quantlab.workbench.catalog_browser import list_catalog_datasets
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.watchlist import load_watchlist, save_watchlist

    assert LIVE_BLOCKED is True
    root = Path("/tmp/quantlab-smoke-f30-universe")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke30")
    state = WorkbenchState(session=session)
    state.ensure_session()

    saved = save_watchlist(session.watchlist_path, {"version": 1, "symbols": ["SMOKE"]})
    assert load_watchlist(session.watchlist_path) == saved
    put = handle_put_watchlist(state, {"add": ["QLAB"]})
    assert put["ok"] is True
    assert put["live_blocked"] is True
    assert "QLAB" in put["symbols"]
    got = handle_get_watchlist(state)
    assert "SMOKE" in got["symbols"]

    uni = handle_get_universe(state)
    assert uni["ok"] is True
    assert uni["live_blocked"] is True
    assert any(s["symbol"] == "QLAB" for s in uni["symbols"])

    cat = handle_get_catalog(state)
    assert cat["ok"] is True
    assert cat["read_only"] is True
    assert isinstance(cat["datasets"], list)
    # Empty-ok si no hay archivo local (no crea DB).
    offline = list_catalog_datasets(catalog_path=Path("/tmp/quantlab-no-such-catalog.sqlite"))
    assert offline["available"] is False
    assert offline["datasets"] == []


def check_f31_features_store() -> None:
    """F31: feature store list + pipeline persist + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_features_store,
        handle_post_lab_features,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = Path("/tmp/quantlab-smoke-f31-features")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke31")
    state = WorkbenchState(session=session)
    state.ensure_session()

    empty = handle_get_lab_features_store(state)
    assert empty["ok"] is True
    assert empty["read_only"] is True
    assert empty["live_blocked"] is True
    assert empty["source"] == "session"
    assert isinstance(empty["artifacts"], list)

    run = handle_post_lab_features(state, {"n_bars": 10})
    assert run["ok"] is True
    assert run["persisted"] is True
    assert run["live_routing"] is False
    assert "log_return" in run["columns"]
    assert Path(run["store_ref"]["path"]).is_file()

    listed = handle_get_lab_features_store(state)
    assert listed["count"] >= 1
    assert listed["live_blocked"] is True


def check_f32_validation_runner() -> None:
    """F32: validation run + persist + anti-leakage + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_validation,
        handle_post_lab_validation_run,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = Path("/tmp/quantlab-smoke-f32-validation")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke32")
    state = WorkbenchState(session=session)
    state.ensure_session()

    preview = handle_get_lab_validation(state)
    assert preview["ok"] is True
    assert "anti_leakage" in preview
    assert preview["walk_forward"]["n_folds"] >= 1

    run = handle_post_lab_validation_run(state, {"n_bars": 40})
    assert run["ok"] is True
    assert run["persisted"] is True
    assert run["live_routing"] is False
    assert run["anti_leakage"]["ok"] is True
    assert Path(run["path"]).is_file()
    assert run["train_val_oos"]["segments"]["train"]["start_idx"] == 0

    listed = handle_get_lab_validation(state)
    assert listed["count"] >= 1
    assert listed["persisted"] is True
    assert listed["live_blocked"] is True


def check_f33_optimizer_history() -> None:
    """F33: optimize + Pareto + persist history + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_optimize_history,
        handle_post_lab_optimize,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = Path("/tmp/quantlab-smoke-f33-optimizer")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke33")
    state = WorkbenchState(session=session)
    state.ensure_session()

    empty = handle_get_lab_optimize_history(state)
    assert empty["ok"] is True
    assert empty["kind"] == "optimize_history"

    run = handle_post_lab_optimize(state, {"lookbacks": [2, 3], "quantities": ["1"], "n_bars": 16})
    assert run["ok"] is True
    assert run["persisted"] is True
    assert run["live_routing"] is False
    assert run["pareto"] is not None
    assert run["pareto"]["n_front"] >= 1
    assert Path(run["path"]).is_file()

    listed = handle_get_lab_optimize_history(state)
    assert listed["count"] >= 1
    assert listed["persisted"] is True
    assert listed["live_blocked"] is True


def check_f34_mc_export() -> None:
    """F34: montecarlo history + HB exports list + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_lab_exports,
        handle_get_lab_montecarlo_history,
        handle_post_lab_export_hb,
        handle_post_lab_montecarlo,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    root = Path("/tmp/quantlab-smoke-f34-mc-export")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke34")
    state = WorkbenchState(session=session)
    state.ensure_session()

    empty = handle_get_lab_montecarlo_history(state)
    assert empty["ok"] is True
    assert empty["kind"] == "montecarlo_history"

    run = handle_post_lab_montecarlo(state, {"n_scenarios": 3, "n_bars": 12})
    assert run["ok"] is True
    assert run["persisted"] is True
    assert run["live_routing"] is False
    assert run["ci_low"] is not None
    assert Path(run["path"]).is_file()

    listed = handle_get_lab_montecarlo_history(state)
    assert listed["count"] >= 1
    assert listed["persisted"] is True
    assert listed["live_blocked"] is True

    exp = handle_post_lab_export_hb(
        state, {"experiment_id": "wb-hb-export", "strategy_version": "demo-1"}
    )
    assert exp["ok"] is True
    assert exp["live_routing"] is False
    assert Path(exp["path"]).is_file()

    exports = handle_get_lab_exports(state)
    assert exports["ok"] is True
    assert exports["count"] >= 1
    assert exports["live_routing"] is False


def check_f35_commands() -> None:
    """F35: /api/commands registry + LIVE_BLOCKED + no live actions."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import WorkbenchState, handle_get_commands
    from quantlab.workbench.commands import PANE_SHORTCUT_ORDER, list_commands
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    payload = list_commands()
    assert payload["ok"] is True
    assert payload["kind"] == "commands"
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert payload["count"] >= 20
    assert payload["pane_shortcut_order"] == list(PANE_SHORTCUT_ORDER)
    ids = {c["id"] for c in payload["commands"]}
    assert "open.health" in ids
    assert "action.health_refresh" in ids
    assert "action.close_focused" in ids
    for cmd in payload["commands"]:
        assert cmd["safe"] is True
        assert cmd["live"] is False

    root = Path("/tmp/quantlab-smoke-f35-commands")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke35")
    state = WorkbenchState(session=session)
    body = handle_get_commands(state)
    assert body["ok"] is True
    assert body["count"] == len(body["commands"])


def check_f36_settings() -> None:
    """F36: settings.json + GET/PUT /api/settings + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_settings,
        handle_put_settings,
    )
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.settings import default_settings, load_settings, save_settings

    assert LIVE_BLOCKED is True
    defaults = default_settings()
    assert defaults["locale"] == "es"
    assert defaults["theme"] == "slate"

    root = Path("/tmp/quantlab-smoke-f36-settings")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke36")
    state = WorkbenchState(session=session)
    state.ensure_session()

    got = handle_get_settings(state)
    assert got["ok"] is True
    assert got["kind"] == "settings"
    assert got["live_blocked"] is True
    assert got["live_routing"] is False
    assert got["settings"]["locale"] == "es"

    put = handle_put_settings(
        state,
        {
            "theme": "high-contrast",
            "default_venue": "paper",
            "default_strategy": "momentum",
            "slippage_bps": "7",
            "locale": "es",
        },
    )
    assert put["ok"] is True
    assert put["settings"]["theme"] == "high-contrast"
    assert session.settings_path.is_file()
    loaded = load_settings(session.settings_path)
    assert loaded["default_venue"] == "paper"
    saved = save_settings(session.settings_path, loaded)
    assert saved["locale"] == "es"


def check_f37_onboarding() -> None:
    """F37: onboarding meta + GET/POST /api/onboarding + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_onboarding,
        handle_post_onboarding_complete,
    )
    from quantlab.workbench.onboarding import ONBOARDING_STEPS, is_onboarding_done
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert len(ONBOARDING_STEPS) == 4

    root = Path("/tmp/quantlab-smoke-f37-onboarding")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke37")
    # Reset flag for idempotent smoke reruns
    meta = session.load_meta()
    meta.pop("onboarding_done", None)
    meta.pop("onboarding_completed_at", None)
    session.save_meta(meta)

    state = WorkbenchState(session=session)
    state.ensure_session()
    got = handle_get_onboarding(state)
    assert got["ok"] is True
    assert got["kind"] == "onboarding"
    assert got["onboarding_done"] is False
    assert got["show_wizard"] is True
    assert got["live_blocked"] is True
    assert got["live_routing"] is False

    done = handle_post_onboarding_complete(state, {})
    assert done["onboarding_done"] is True
    assert done["show_wizard"] is False
    assert is_onboarding_done(session.load_meta()) is True


def check_f38_docs_help() -> None:
    """F38: docs list/content + path traversal fail-closed + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_get_docs,
        handle_get_docs_content,
    )
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.docs_browser import list_docs, read_docs_content
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    listed = list_docs()
    assert listed["ok"] is True
    assert listed["count"] >= 1
    paths = {d["path"] for d in listed["docs"]}
    assert any(p.endswith(".md") and "/" not in p for p in paths)
    assert any(p.startswith("ops/") and p.endswith(".md") for p in paths)

    sample = next(iter(paths))
    content = read_docs_content(sample)
    assert content["ok"] is True
    assert "content" in content

    for bad in ("../pyproject.toml", "audit/INTERNAL_AUDIT_F37.md"):
        try:
            read_docs_content(bad)
        except ValidationError:
            pass
        else:
            raise AssertionError(f"expected ValidationError for {bad!r}")

    root = Path("/tmp/quantlab-smoke-f38-docs")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke38")
    state = WorkbenchState(session=session)
    state.ensure_session()
    got = handle_get_docs(state)
    assert got["ok"] is True
    assert got["kind"] == "docs"
    assert got["live_blocked"] is True
    assert got["live_routing"] is False

    body = handle_get_docs_content(state, f"path={sample}")
    assert body["ok"] is True
    assert body["path"] == sample

    try:
        handle_get_docs_content(state, "path=../etc/passwd")
    except ApiError:
        pass
    else:
        raise AssertionError("expected ApiError for path traversal")

    cmds = list_commands()
    ids = {c["id"] for c in cmds["commands"]}
    assert "open.docs" in ids


def check_f39_session_zip() -> None:
    """F39: session export/import ZIP + zip-slip fail-closed + LIVE_BLOCKED."""
    import zipfile
    from pathlib import Path

    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_session_export,
        handle_post_session_import,
    )
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.session_zip import MANIFEST_NAME, export_session, import_session_zip

    assert LIVE_BLOCKED is True
    root = Path("/tmp/quantlab-smoke-f39-zip")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke39")
    (session.reports_dir / "smoke.json").write_text('{"ok":true}\n', encoding="utf-8")
    (session.root / ".env").write_text("NO=1\n", encoding="utf-8")

    result = export_session(session)
    assert result.archive_path.is_file()
    with zipfile.ZipFile(result.archive_path, "r") as zf:
        names = set(zf.namelist())
    assert MANIFEST_NAME in names
    assert ".env" not in names

    imported = import_session_zip(
        result.archive_path,
        session_parent=root,
        mode="new",
        session_id="smoke39b",
    )
    assert imported.session_id == "smoke39b"
    assert (imported.session_root / "reports" / "smoke.json").is_file()

    evil = root / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr(
            MANIFEST_NAME,
            '{"format":"quantlab_session_zip","format_version":1}',
        )
        zf.writestr("../pwn.txt", "x")
    try:
        import_session_zip(evil, session_parent=root, mode="new", session_id="evil39")
    except ValidationError:
        pass
    else:
        raise AssertionError("expected zip-slip ValidationError")

    state = WorkbenchState(session=session)
    state.ensure_session()
    exp = handle_get_session_export(state)
    assert exp["ok"] is True
    assert exp["live_blocked"] is True
    assert exp["live_routing"] is False
    got = handle_post_session_import(
        state,
        {"mode": "new", "session_id": "smoke39c", "zip_path": exp["path"]},
    )
    assert got["ok"] is True
    assert got["session_id"] == "smoke39c"


def check_f40_workspace_presets() -> None:
    """F40: presets research/trading_paper/ops + apply → layout.json."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_presets,
        handle_post_presets_apply,
    )
    from quantlab.workbench.layout import load_layout
    from quantlab.workbench.presets import PRESET_NAMES, apply_preset, list_presets
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    catalog = list_presets()
    assert catalog["count"] == 3
    assert set(PRESET_NAMES) == {"research", "trading_paper", "ops"}
    assert catalog["live_blocked"] is True

    root = Path("/tmp/quantlab-smoke-f40-presets")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke40")
    state = WorkbenchState(session=session)
    state.ensure_session()

    listed = handle_get_presets(state)
    assert listed["ok"] is True
    assert listed["count"] == 3

    applied = handle_post_presets_apply(state, {"name": "research"})
    assert applied["ok"] is True
    assert applied["preset"]["name"] == "research"
    assert set(applied["layout"]["windows"].keys()) == {
        "health",
        "backtest",
        "reports",
        "chat",
    }
    loaded = load_layout(session.layout_path)
    assert "backtest" in loaded["windows"]

    ops = apply_preset(session.layout_path, "ops")
    assert set(ops["layout"]["windows"].keys()) == {
        "health",
        "settings",
        "docs",
        "catalog",
    }


def check_f41_activity_log() -> None:
    """F41: activity.jsonl append-only + GET /api/activity + hooks."""
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.activity import ACTIVITY_EVENT_TYPES, ActivityLog, list_activity
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_get_activity,
        handle_post_broker_connect,
        handle_post_lab_backtest,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert {
        "connect",
        "submit",
        "backtest",
        "optimize",
        "export",
        "error",
    } == ACTIVITY_EVENT_TYPES

    root = Path("/tmp/quantlab-smoke-f41-activity")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke41")
    state = WorkbenchState(session=session)
    state.ensure_session()
    assert session.activity_path.is_file()

    connected = handle_post_broker_connect(
        state, {"venue": "binance", "mode": "tester", "md_source": "fake"}
    )
    assert connected["ok"] is True

    bt = handle_post_lab_backtest(
        state,
        {"strategy_id": "momentum", "n_bars": 12, "experiment_id": "smoke-f41-bt"},
    )
    assert bt is not None

    try:
        handle_post_broker_connect(state, {"venue": ""})
        raise AssertionError("expected ApiError for empty venue")
    except ApiError:
        pass

    listed = handle_get_activity(state, "limit=100")
    assert listed["ok"] is True
    assert listed["kind"] == "activity"
    assert listed["live_blocked"] is True
    events = {e["event"] for e in listed["events"]}
    assert "connect" in events
    assert "backtest" in events
    assert "error" in events

    # Append-only direct write
    ActivityLog(session.activity_path).append("export", message="smoke-export")
    again = list_activity(session.activity_path, limit=50)
    assert any(e["event"] == "export" for e in again["events"])


def check_f42_ops_metrics() -> None:
    """F42: ops metrics JSON + prometheus text + live_gate.blocked."""
    from pathlib import Path

    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import LIVE_BLOCKED, assert_live_routing_blocked
    from quantlab.infra.ops_metrics import get_ops_metrics
    from quantlab.workbench.api import (
        WorkbenchState,
        handle_get_ops_metrics,
        handle_get_ops_prometheus,
    )
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    metrics = get_ops_metrics()
    metrics.reset()
    metrics.inc("health.runs", 1)
    try:
        assert_live_routing_blocked()
        raise AssertionError("expected ValidationError from live gate")
    except ValidationError:
        pass

    root = Path("/tmp/quantlab-smoke-f42-ops")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke42")
    state = WorkbenchState(session=session)
    state.ensure_session()

    payload = handle_get_ops_metrics(state)
    assert payload["ok"] is True
    assert payload["kind"] == "ops_metrics"
    assert payload["live_blocked"] is True
    assert payload["live_routing"] is False
    assert payload["counters"]["health.runs"] >= 1
    assert payload["live_gate_blocked"] >= 1
    assert payload["highlight_live_gate_blocked"] is True

    text = handle_get_ops_prometheus(state)
    assert "live_gate_blocked" in text
    assert "# TYPE" in text

    ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.ops_metrics" in ids
    metrics.reset()


def check_f43_redteam() -> None:
    """F43: zip sandbox, create_server loopback gate, body 2MiB, LIVE reject."""
    from pathlib import Path

    from quantlab.core.exceptions import ValidationError
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import ApiError, WorkbenchState, handle_post_mode
    from quantlab.workbench.server import DEFAULT_MAX_BODY_BYTES, create_server
    from quantlab.workbench.session import WorkbenchSession, validate_session_id
    from quantlab.workbench.session_zip import resolve_upload_archive

    assert LIVE_BLOCKED is True
    assert DEFAULT_MAX_BODY_BYTES == 2_000_000

    try:
        validate_session_id("../evil")
        raise AssertionError("session_id traversal should raise")
    except ValidationError:
        pass

    try:
        create_server(host="0.0.0.0", port=0, allow_non_loopback=False)
        raise AssertionError("create_server unbound without flag should raise")
    except ValidationError:
        pass

    root = Path("/tmp/quantlab-smoke-f43-rt")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    parent = root / "sessions"
    session = WorkbenchSession.create_or_load(parent, "smoke43")
    state = WorkbenchState(session=session)
    state.ensure_session()

    outside = root / "evil.zip"
    outside.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    try:
        resolve_upload_archive(
            zip_path=str(outside),
            zip_base64=None,
            work_dir=root / "w",
            allowed_roots=(parent.resolve(),),
        )
        raise AssertionError("zip_path outside sandbox should raise")
    except ValidationError:
        pass

    try:
        handle_post_mode(state, {"mode": "live"})
        raise AssertionError("LIVE mode should be rejected")
    except ApiError as exc:
        assert exc.status == 400


def check_f44_e2e_paper_workflow() -> None:
    """F44: flujo paper E2E vía handlers (sin browser) + LIVE reject."""
    import shutil
    from pathlib import Path

    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_get_health,
        handle_get_lab_reports,
        handle_get_paper_book,
        handle_get_positions,
        handle_get_session_export,
        handle_post_broker_connect,
        handle_post_lab_backtest,
        handle_post_lab_export_hb,
        handle_post_lab_montecarlo,
        handle_post_lab_optimize,
        handle_post_lab_validation_run,
        handle_post_mode,
        handle_post_paper_session_start,
        handle_post_paper_session_step,
        handle_post_paper_session_stop,
        handle_post_paper_submit,
    )
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True

    root = Path("/tmp/quantlab-smoke-f44-e2e")
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root / "sessions", "smoke44")
    state = WorkbenchState(session=session)
    state.ensure_session()

    health = handle_get_health(state)
    assert health.get("ok") is True or health.get("live_blocked") is True
    assert health["live_blocked"] is True

    mode = handle_post_mode(state, {"mode": "paper"})
    assert mode["mode"] == "paper"

    connect = handle_post_broker_connect(state, {"venue": "binance", "mode": "tester"})
    assert connect["ok"] is True
    assert connect["paper_broker"] is True

    connect_a3 = handle_post_broker_connect(
        state, {"venue": "a3", "mode": "tester", "md_source": "fake"}
    )
    assert connect_a3["paper_broker"] is True

    # Reconnect binance for submit path
    handle_post_broker_connect(state, {"venue": "binance", "mode": "tester"})
    broker = state.broker
    assert broker is not None
    symbol = broker.list_instruments()[0].symbol

    submit = handle_post_paper_submit(
        state,
        {
            "intent_type": "place_order",
            "instrument_id": symbol,
            "side": "buy",
            "quantity": "1",
            "order_type": "market",
        },
    )
    assert submit["ack"]["status"] == "FILLED"

    positions = handle_get_positions(state)
    assert len(positions["positions"]) >= 1
    book = handle_get_paper_book(state)
    assert "cash" in book["book"]

    start = handle_post_paper_session_start(
        state,
        {"strategy_id": "buy_once", "symbol": symbol, "max_steps": 3},
    )
    assert start["ok"] is True
    step = handle_post_paper_session_step(state)
    assert step["step"] == 1
    handle_post_paper_session_stop(state)

    bt = handle_post_lab_backtest(
        state,
        {
            "strategy_id": "momentum",
            "n_bars": 16,
            "params": {"lookback": 2, "quantity": "1"},
            "experiment_id": "smoke44-bt",
        },
    )
    assert bt["ok"] is True
    reports = handle_get_lab_reports(state)
    assert reports.get("count", 0) >= 1 or len(reports.get("reports", [])) >= 1

    val = handle_post_lab_validation_run(state, {"n_bars": 40, "train_size": 10, "test_size": 5})
    assert val["ok"] is True
    opt = handle_post_lab_optimize(state, {"lookbacks": [2], "quantities": ["1"], "n_bars": 16})
    assert opt["ok"] is True
    mc = handle_post_lab_montecarlo(state, {"n_scenarios": 2, "n_bars": 12, "persist": True})
    assert mc["ok"] is True

    hb = handle_post_lab_export_hb(
        state, {"experiment_id": "smoke44-hb", "strategy_version": "demo"}
    )
    assert hb["ok"] is True

    exported = handle_get_session_export(state)
    assert exported["ok"] is True
    assert Path(str(exported["path"])).is_file()

    try:
        handle_post_mode(state, {"mode": "live"})
        raise AssertionError("LIVE mode should be rejected")
    except ApiError as exc:
        assert exc.status == 400
    assert LIVE_BLOCKED is True


def check_f45_about() -> None:
    """F45: GET /api/about + version badge UI assets + LIVE_BLOCKED."""
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY, build_about_payload
    from quantlab.workbench.api import WorkbenchState, handle_get_about
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.server import STATIC_ROOT
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"

    root = Path("/tmp/quantlab-smoke-f45-about")
    root.mkdir(parents=True, exist_ok=True)
    session = WorkbenchSession.create_or_load(root, "smoke45")
    state = WorkbenchState(session=session, bind_host="127.0.0.1", allow_non_loopback=False)
    state.ensure_session()

    about = handle_get_about(state)
    assert about["ok"] is True
    assert about["kind"] == "about"
    assert about["version"] == "0.49.0"
    assert about["live_blocked"] is True
    assert about["phases_summary"] == PHASES_SUMMARY
    assert about["python_version"]
    assert about["bind_policy"]["policy"] == "loopback-default"

    built = build_about_payload(bind_host="0.0.0.0", allow_non_loopback=True)
    assert built["bind_policy"]["policy"] == "allow-non-loopback"

    ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.about" in ids

    assert (STATIC_ROOT / "js" / "about.js").is_file()
    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    assert "about.js" in html
    assert 'data-open="about"' in html
    assert "sb-version" in html
    shell = (STATIC_ROOT / "js" / "shell.js").read_text(encoding="utf-8")
    assert "openAbout" in shell
    assert "refreshVersionBadge" in shell


def check_f46_sessions() -> None:
    """F46: multi-session list/switch/new + UI + LIVE_BLOCKED."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import (
        ApiError,
        WorkbenchState,
        handle_get_sessions,
        handle_post_sessions_new,
        handle_post_sessions_switch,
    )
    from quantlab.workbench.commands import list_commands
    from quantlab.workbench.server import STATIC_ROOT
    from quantlab.workbench.session import WorkbenchSession, list_sessions

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f46-"))
    parent = root / "sessions"
    parent.mkdir(parents=True, exist_ok=True)
    s1 = WorkbenchSession.create_or_load(parent, "smoke46a")
    WorkbenchSession.create_or_load(parent, "smoke46b")
    state = WorkbenchState(session=s1, session_parent=parent)
    state.ensure_session()

    listed = handle_get_sessions(state)
    assert listed["ok"] is True
    assert listed["kind"] == "sessions"
    assert listed["count"] >= 2
    assert listed["session_id"] == "smoke46a"
    assert listed["live_blocked"] is True

    ids = {i["session_id"] for i in list_sessions(parent)}
    assert "smoke46a" in ids and "smoke46b" in ids

    switched = handle_post_sessions_switch(state, {"session_id": "smoke46b"})
    assert switched["ok"] is True
    assert switched["session_id"] == "smoke46b"

    created = handle_post_sessions_new(state, {"session_id": "smoke46c"})
    assert created["ok"] is True
    assert created["session_id"] == "smoke46c"

    try:
        handle_post_sessions_switch(state, {"session_id": "../evil"})
        raise AssertionError("path traversal should fail")
    except ApiError as exc:
        assert exc.status == 400

    cmd_ids = {c["id"] for c in list_commands()["commands"]}
    assert "open.sessions" in cmd_ids

    assert (STATIC_ROOT / "js" / "panes" / "sessions.js").is_file()
    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    assert "sessions.js" in html
    assert 'data-open="sessions"' in html
    shell = (STATIC_ROOT / "js" / "shell.js").read_text(encoding="utf-8")
    assert "openSessions" in shell
    api = (STATIC_ROOT / "js" / "api.js").read_text(encoding="utf-8")
    assert "sessionsList" in api
    assert "/api/sessions/switch" in api


def check_f48_themes() -> None:
    """F48: theme CSS tokens + settings theme roundtrip + data-theme JS."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_settings, handle_put_settings
    from quantlab.workbench.server import STATIC_ROOT
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.settings import load_settings

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"

    css = (STATIC_ROOT / "css" / "workbench.css").read_text(encoding="utf-8")
    for token in (
        "--bg-banner",
        "--bg-status",
        "--bg-taskbar",
        "--bg-desktop-a",
        "--amber-soft",
        "--shadow-modal",
        'html[data-theme="high-contrast"]',
        'html[data-theme="slate"]',
    ):
        assert token in css, token

    html = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    assert 'data-theme="slate"' in html

    shell = (STATIC_ROOT / "js" / "shell.js").read_text(encoding="utf-8")
    assert 'document.documentElement.setAttribute("data-theme"' in shell
    settings_js = (STATIC_ROOT / "js" / "panes" / "settings.js").read_text(encoding="utf-8")
    assert 'document.documentElement.setAttribute("data-theme"' in settings_js

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f48-"))
    session = WorkbenchSession.create_or_load(root, "smoke48")
    state = WorkbenchState(session=session)
    state.ensure_session()

    got = handle_get_settings(state)
    assert got["ok"] is True
    assert got["settings"]["theme"] == "slate"

    put = handle_put_settings(state, {"theme": "high-contrast", "locale": "es"})
    assert put["ok"] is True
    assert put["settings"]["theme"] == "high-contrast"
    assert put["live_blocked"] is True
    assert load_settings(session.settings_path)["theme"] == "high-contrast"

    put2 = handle_put_settings(state, {"theme": "slate"})
    assert put2["settings"]["theme"] == "slate"
    assert load_settings(session.settings_path)["theme"] == "slate"


def check_f50_perf_baseline() -> None:
    """F50: workbench API latency baseline p95/max < 500ms (loopback)."""
    import tempfile
    import threading
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.perf_baseline import (
        DEFAULT_MAX_THRESHOLD_MS,
        DEFAULT_P95_THRESHOLD_MS,
        PERF_ENDPOINTS,
        assert_baseline_within_budget,
        run_perf_baseline,
    )
    from quantlab.workbench.server import create_server
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f50-"))
    session = WorkbenchSession.create_or_load(root, "smoke50")
    state = WorkbenchState(session=session)
    state.ensure_session()
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        report = run_perf_baseline(
            server,
            endpoints=PERF_ENDPOINTS,
            samples=15,
            warmup=2,
            p95_threshold_ms=DEFAULT_P95_THRESHOLD_MS,
            max_threshold_ms=DEFAULT_MAX_THRESHOLD_MS,
            version=__version__,
            live_blocked=True,
        )
        assert_baseline_within_budget(report)
        assert len(report.endpoints) == 5
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def check_f51_rate_limit() -> None:
    """F51: soft rate limit in-process; 429 JSON con límite bajo inyectado."""
    import http.client
    import json
    import tempfile
    import threading
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState
    from quantlab.workbench.rate_limit import (
        DEFAULT_RATE_LIMIT_RPS,
        RateLimitConfig,
    )
    from quantlab.workbench.server import create_server
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"
    assert DEFAULT_RATE_LIMIT_RPS >= 120.0

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f51-"))
    session = WorkbenchSession.create_or_load(root, "smoke51")
    state = WorkbenchState(session=session)
    state.ensure_session()
    state.configure_rate_limit(
        RateLimitConfig(enabled=True, requests_per_second=2.0, burst=2.0)
    )
    server = create_server(host="127.0.0.1", port=0, state=state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        assert isinstance(host, str)
        assert isinstance(port, int)
        statuses: list[int] = []
        for _ in range(4):
            conn = http.client.HTTPConnection(host, port, timeout=5.0)
            try:
                conn.request("GET", "/api/mode")
                resp = conn.getresponse()
                raw = resp.read()
                statuses.append(resp.status)
                if resp.status == 429:
                    body = json.loads(raw.decode("utf-8"))
                    assert body["ok"] is False
                    assert body["code"] == "rate_limit_exceeded"
                    assert resp.getheader("Retry-After") is not None
            finally:
                conn.close()
        assert statuses.count(200) == 2
        assert statuses.count(429) >= 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)



def check_f52_shutdown() -> None:
    """F52: graceful shutdown stops paper session; /api/shutdown loopback-only."""
    import tempfile
    from datetime import UTC, datetime
    from decimal import Decimal
    from pathlib import Path

    from quantlab import __version__
    from quantlab.brokers.paper.book import PaperBook
    from quantlab.brokers.paper.broker import PaperBroker
    from quantlab.brokers.types import (
        BrokerAccount,
        BrokerAck,
        BrokerInstrument,
        BrokerPosition,
        BrokerSnapshot,
    )
    from quantlab.core.types.orders import OrderIntent
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import ApiError, WorkbenchState, handle_post_shutdown
    from quantlab.workbench.paper_session import PaperSessionConfig, PaperSessionRunner
    from quantlab.workbench.risk import PaperRiskLimits
    from quantlab.workbench.session import WorkbenchSession
    from quantlab.workbench.shutdown import perform_graceful_shutdown

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"

    class _Md:
        symbol = "TEST"

        @property
        def venue_id(self) -> str:
            return "md"

        def connect(self) -> dict[str, object]:
            return {"ok": True}

        def close(self) -> dict[str, object]:
            return {"ok": True}

        def health(self) -> dict[str, object]:
            return {"ok": True}

        def list_instruments(self) -> list[BrokerInstrument]:
            return [
                BrokerInstrument(
                    symbol="TEST",
                    description="t",
                    currency="USD",
                    status="ACTIVE",
                )
            ]

        def get_snapshot(self, symbol: str) -> BrokerSnapshot:
            return BrokerSnapshot(
                symbol=symbol,
                bid=Decimal("99"),
                ask=Decimal("101"),
                last=Decimal("100"),
                ts=datetime(2024, 1, 1, tzinfo=UTC),
            )

        def get_account(self) -> BrokerAccount:
            return BrokerAccount(cash=Decimal("1"), currency="USD")

        def get_positions(self) -> list[BrokerPosition]:
            return []

        def submit(self, intent: OrderIntent) -> BrokerAck:
            raise AssertionError("no md submit")

        def cancel(self, order_id: str) -> BrokerAck:
            raise AssertionError("no md cancel")

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f52-"))
    session = WorkbenchSession.create_or_load(root, "smoke52")
    state = WorkbenchState(session=session, slippage_bps=Decimal("3"))
    state.ensure_session()
    book = PaperBook(initial_cash=Decimal("10000"))
    broker = PaperBroker(_Md(), book=book)  # type: ignore[arg-type]
    state.broker = broker
    state.book = book
    runner = PaperSessionRunner(broker, PaperRiskLimits(), book)
    runner.start(PaperSessionConfig(strategy_id="buy_once", symbol="TEST", max_steps=10))
    state.paper_session = runner
    assert runner.status()["running"] is True

    try:
        handle_post_shutdown(state, client_ip="8.8.8.8", stop_server=False)
        raise AssertionError("expected 403 for non-loopback")
    except ApiError as exc:
        assert exc.status == 403

    result = perform_graceful_shutdown(state, reason="smoke-f52", stop_server=False)
    assert result["ok"] is True
    assert result["paper"]["stopped"] is True
    assert state.paper_session is None
    assert state.shutdown_requested is True
    assert session.settings_path.is_file()


def check_f53_dockerfile() -> None:
    """F53: Dockerfile.workbench CMD allow-non-loopback / no-browser (parse file)."""
    import re
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"

    root = Path(__file__).resolve().parents[1]
    dockerfile = root / "Dockerfile.workbench"
    dockerignore = root / ".dockerignore"
    ops = root / "docs" / "ops" / "DOCKER_WORKBENCH.md"
    assert dockerfile.is_file()
    assert dockerignore.is_file()
    assert ops.is_file()

    text = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in text
    assert "uv sync" in text
    assert "EXPOSE 8765" in text
    match = re.search(r"^CMD\s+\[(.+)\]\s*$", text, flags=re.MULTILINE)
    assert match is not None
    tokens = [tok.strip().strip('"').strip("'") for tok in match.group(1).split(",")]
    assert "quantlab-workbench" in tokens
    assert "--allow-non-loopback" in tokens
    assert "--no-browser" in tokens
    assert "0.0.0.0" in tokens
    assert "127.0.0.1:8765:8765" in ops.read_text(encoding="utf-8")
    di = dockerignore.read_text(encoding="utf-8")
    assert ".env" in di
    assert "data/" in di or "data" in di


def check_f54_probes() -> None:
    """F54: /api/livez always alive; /api/readyz LIVE_BLOCKED + writable."""
    import tempfile
    from pathlib import Path

    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api import WorkbenchState, handle_get_livez, handle_get_readyz
    from quantlab.workbench.probes import readyz_payload
    from quantlab.workbench.session import WorkbenchSession

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"

    root = Path(tempfile.mkdtemp(prefix="quantlab-smoke-f54-"))
    session = WorkbenchSession.create_or_load(root, "smoke54")
    state = WorkbenchState(session=session)
    state.ensure_session()

    live = handle_get_livez(state)
    assert live["ok"] is True
    assert live["alive"] is True
    assert live["status"] == "alive"

    ready = handle_get_readyz(state)
    assert ready["ready"] is True
    assert ready["checks"]["live_blocked"] is True
    assert ready["checks"]["session_root_writable"] is True

    not_ready = readyz_payload(session_root=session.root, live_blocked=False)
    assert not_ready["ready"] is False
    assert not_ready["status"] == "not_ready"

    ops = Path(__file__).resolve().parents[1] / "docs" / "ops" / "DOCKER_WORKBENCH.md"
    ops_text = ops.read_text(encoding="utf-8")
    assert "/api/livez" in ops_text
    assert "/api/readyz" in ops_text


def check_f55_openapi() -> None:
    """F55: OpenAPI catalog has health/livez; no LIVE trading routes."""
    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.api_catalog import (
        OPENAPI_PATH,
        assert_no_live_trading_routes,
        build_openapi_schema,
        catalog_routes,
    )

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"

    routes = catalog_routes()
    paths = {(r.method, r.path) for r in routes}
    assert ("GET", "/api/health") in paths
    assert ("GET", "/api/livez") in paths
    assert ("GET", OPENAPI_PATH) in paths

    schema = build_openapi_schema()
    assert schema["openapi"].startswith("3.")
    assert "/api/health" in schema["paths"]
    assert "/api/livez" in schema["paths"]
    for path in schema["paths"]:
        assert path != "/api/live"
        assert not path.startswith("/api/live/")
    assert_no_live_trading_routes()
    assert schema["x-quantlab"]["live_blocked"] is True
    assert schema["x-quantlab"]["phases_summary"] == PHASES_SUMMARY


def check_f56_security_headers() -> None:
    """F56: security headers + CORS fail-closed (no ACAO *)."""
    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.security_headers import (
        SECURITY_HEADERS,
        cors_allow_origin,
        security_header_items,
        wants_api_no_store,
    )

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"
    assert SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
    assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"
    assert SECURITY_HEADERS["Referrer-Policy"] == "no-referrer"
    assert wants_api_no_store("/api/health") is True
    assert cors_allow_origin("*") is None
    assert cors_allow_origin("https://evil.example") is None
    assert cors_allow_origin("http://127.0.0.1:8765") == "http://127.0.0.1:8765"
    items = dict(security_header_items(path="/api/about", origin="https://evil.example"))
    assert items["Cache-Control"] == "no-store"
    assert "Access-Control-Allow-Origin" not in items


def check_f57_csp() -> None:
    """F57: Content-Security-Policy restrictiva (sin unsafe-eval)."""
    from quantlab import __version__
    from quantlab.execution.live_gate import LIVE_BLOCKED
    from quantlab.workbench.about import PHASES_SUMMARY
    from quantlab.workbench.security_headers import (
        CONTENT_SECURITY_POLICY,
        SECURITY_HEADERS,
        security_header_items,
    )

    assert LIVE_BLOCKED is True
    assert __version__ == "0.49.0"
    assert PHASES_SUMMARY == "F19–F57 INTERNAL"
    csp = CONTENT_SECURITY_POLICY
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "connect-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "unsafe-eval" not in csp
    assert SECURITY_HEADERS["Content-Security-Policy"] == csp
    items = dict(security_header_items(path="/", origin=None))
    assert items["Content-Security-Policy"] == csp


def main() -> int:
    checks: list[tuple[str, Callable[[], None]]] = [
        ("LIVE_BLOCKED is True", check_live_blocked),
        ("assert_live_routing_blocked raises", check_live_gate_raises),
        ("brokers imports + REAL=PAPER", check_brokers_imports),
        ("workbench imports", check_workbench_imports),
        ("chat allowlist + FakeProvider", check_chat_safe),
        ("quantlab-health live_blocked", check_health_dict),
        ("about version matches __version__", check_about_version_matches),
        ("paper book + session_id fail-closed", check_paper_book_session),
        ("F23 paper book import", check_f23_book_import),
        ("F24 plugins + generics", check_f24_plugins),
        ("F25 launch --allow-non-loopback", check_f25_launch_parser),
        ("F25 ops desk slip/charset/risk", check_f25_ops_desk_invariants),
        ("F26 paper session runner", check_f26_paper_session),
        ("F27 strategy catalog", check_f27_strategy_catalog),
        ("F28 layout + journal API", check_f28_layout_journal),
        ("F29 reports + metrics history", check_f29_reports),
        ("F30 universe watchlist + catalog", check_f30_universe_catalog),
        ("F31 features store + pipeline", check_f31_features_store),
        ("F32 validation walk-forward runner", check_f32_validation_runner),
        ("F33 optimizer history + pareto", check_f33_optimizer_history),
        ("F34 montecarlo history + HB export", check_f34_mc_export),
        ("F35 command palette + /api/commands", check_f35_commands),
        ("F36 settings + status bar", check_f36_settings),
        ("F37 first-run onboarding wizard", check_f37_onboarding),
        ("F38 docs / help browser", check_f38_docs_help),
        ("F39 session export/import ZIP", check_f39_session_zip),
        ("F40 workspace presets", check_f40_workspace_presets),
        ("F41 activity log + toasts API", check_f41_activity_log),
        ("F42 ops metrics panel API", check_f42_ops_metrics),
        ("F43 red-team workbench hardening", check_f43_redteam),
        ("F44 e2e paper workflow integration", check_f44_e2e_paper_workflow),
        ("F45 about dialog + version badge", check_f45_about),
        ("F46 multi-session switcher", check_f46_sessions),
        ("F47 chat context awareness", check_f47_chat_context),
        ("F48 theme CSS slate + high-contrast", check_f48_themes),
        ("F50 workbench API perf baseline", check_f50_perf_baseline),
        ("F51 soft API rate limit", check_f51_rate_limit),
        ("F52 graceful shutdown paper safety", check_f52_shutdown),
        ("F53 Dockerfile workbench opt-in", check_f53_dockerfile),
        ("F54 readiness / liveness probes", check_f54_probes),
        ("F55 OpenAPI / API catalog", check_f55_openapi),
        ("F56 security headers + CORS", check_f56_security_headers),
        ("F57 Content-Security-Policy", check_f57_csp),
    ]
    ok = True
    for name, fn in checks:
        ok = _check(name, fn) and ok
    print("—" * 40)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
