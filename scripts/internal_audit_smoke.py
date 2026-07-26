#!/usr/bin/env python3
"""Smoke INTERNAL Zero-Trust — invariantes LIVE + imports workbench/brokers.

Uso:
  uv run python scripts/internal_audit_smoke.py

Exit 0 = all PASS; exit 1 = algún FAIL.
"""

from __future__ import annotations

import sys
from typing import Callable


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
    from quantlab.brokers.mode import REAL_ALIAS, OperatingMode, ModeGuard
    from quantlab.brokers.registry import get_default_registry

    assert REAL_ALIAS is OperatingMode.PAPER
    assert OperatingMode.LIVE in OperatingMode
    _ = ModeGuard
    reg = get_default_registry()
    venues = set(reg.list_venues())
    assert {"a3", "binance", "paper"}.issubset(venues), venues


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
    from quantlab.infra.health import run_health_checks

    report = run_health_checks().to_dict()
    assert report.get("ok") is True
    assert report.get("live_blocked") is True


def main() -> int:
    checks: list[tuple[str, Callable[[], None]]] = [
        ("LIVE_BLOCKED is True", check_live_blocked),
        ("assert_live_routing_blocked raises", check_live_gate_raises),
        ("brokers imports + REAL=PAPER", check_brokers_imports),
        ("workbench imports", check_workbench_imports),
        ("chat allowlist + FakeProvider", check_chat_safe),
        ("quantlab-health live_blocked", check_health_dict),
    ]
    ok = True
    for name, fn in checks:
        ok = _check(name, fn) and ok
    print("—" * 40)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
