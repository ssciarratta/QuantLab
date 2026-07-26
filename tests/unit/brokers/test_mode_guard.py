"""Tests ModeGuard / resolve_mode / default_mode."""

from __future__ import annotations

import pytest

from quantlab.brokers.mode import (
    REAL_ALIAS,
    ModeGuard,
    OperatingMode,
    default_mode,
    resolve_mode,
)
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED


def test_live_blocked_invariant() -> None:
    assert LIVE_BLOCKED is True


def test_default_mode_is_tester() -> None:
    assert default_mode() is OperatingMode.TESTER


def test_real_alias_is_paper() -> None:
    assert REAL_ALIAS is OperatingMode.PAPER
    assert resolve_mode("real") is OperatingMode.PAPER
    assert resolve_mode("REAL") is OperatingMode.PAPER


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("tester", OperatingMode.TESTER),
        ("TESTER", OperatingMode.TESTER),
        ("paper", OperatingMode.PAPER),
        ("Paper", OperatingMode.PAPER),
        ("live", OperatingMode.LIVE),
        ("LIVE", OperatingMode.LIVE),
    ],
)
def test_resolve_mode_case_insensitive(name: str, expected: OperatingMode) -> None:
    assert resolve_mode(name) is expected


def test_resolve_mode_unknown() -> None:
    with pytest.raises(ValidationError, match="modo desconocido"):
        resolve_mode("sandbox")


def test_mode_guard_allows_tester_and_paper() -> None:
    ModeGuard.validate_boot(OperatingMode.TESTER)
    ModeGuard.validate_boot(OperatingMode.PAPER)


def test_mode_guard_blocks_live_when_live_blocked() -> None:
    assert LIVE_BLOCKED is True
    with pytest.raises(ValidationError, match="LIVE_BLOCKED"):
        ModeGuard.validate_boot(OperatingMode.LIVE)
