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

    reg = ToolRegistry(WorkbenchState())
    for bad in ("submit_order", "place_order", "set_live", "flip_live_blocked"):
        try:
            reg.call(bad)
        except ValidationError:
            continue
        raise AssertionError(f"expected reject for {bad}")


def check_health_dict() -> None:
    from quantlab import __version__
    from quantlab.infra.health import run_health_checks

    report = run_health_checks().to_dict()
    assert report.get("ok") is True
    assert report.get("live_blocked") is True
    assert report.get("version") == __version__


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


def main() -> int:
    checks: list[tuple[str, Callable[[], None]]] = [
        ("LIVE_BLOCKED is True", check_live_blocked),
        ("assert_live_routing_blocked raises", check_live_gate_raises),
        ("brokers imports + REAL=PAPER", check_brokers_imports),
        ("workbench imports", check_workbench_imports),
        ("chat allowlist + FakeProvider", check_chat_safe),
        ("quantlab-health live_blocked", check_health_dict),
        ("paper book + session_id fail-closed", check_paper_book_session),
        ("F23 paper book import", check_f23_book_import),
        ("F24 plugins + generics", check_f24_plugins),
        ("F25 launch --allow-non-loopback", check_f25_launch_parser),
        ("F25 ops desk slip/charset/risk", check_f25_ops_desk_invariants),
        ("F26 paper session runner", check_f26_paper_session),
        ("F27 strategy catalog", check_f27_strategy_catalog),
        ("F28 layout + journal API", check_f28_layout_journal),
    ]
    ok = True
    for name, fn in checks:
        ok = _check(name, fn) and ok
    print("—" * 40)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
