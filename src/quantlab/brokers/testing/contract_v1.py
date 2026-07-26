"""Cooperative, offline contract checks for Broker Plugin Contract v1."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast

from quantlab.brokers.contracts.v1 import BrokerPluginSpec
from quantlab.brokers.mode import ModeGuard, OperatingMode
from quantlab.brokers.port import BrokerPort
from quantlab.brokers.read_only import ReadOnlyBrokerPort
from quantlab.brokers.registry import BrokerRegistry
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.orders import OrderIntent


@dataclass(frozen=True, slots=True)
class BrokerContractReport:
    """Immutable result of a cooperative plugin contract run."""

    passed: bool
    checks: tuple[str, ...]
    issues: tuple[str, ...]


def run_broker_contract(
    spec: BrokerPluginSpec,
    mode: OperatingMode = OperatingMode.TESTER,
) -> BrokerContractReport:
    """Run v1 checks without credentials, network isolation, or execution calls.

    The plugin must provide deterministic/offline behavior. This test kit is not
    a security sandbox and never invokes the plugin's ``submit`` or ``cancel``.
    """
    checks: list[str] = []
    issues: list[str] = []

    try:
        ModeGuard.validate_boot(mode)
    except ValidationError as exc:
        return _report(checks, [f"mode: {exc}"])

    try:
        signature = inspect.signature(spec.factory)
        signature.bind(mode)
    except (TypeError, ValueError) as exc:
        return _report(checks, [f"factory.signature: {exc}"])

    try:
        # Exactly one invocation: TypeError from plugin code is reported, never retried.
        broker = spec.factory(mode)
        checks.append("factory.once")
    except Exception as exc:  # noqa: BLE001 - cooperative third-party boundary
        return _report(checks, [f"factory: {_exception_text(exc)}"])

    if not isinstance(broker, BrokerPort):
        return _report(checks, ["broker_port: factory result does not implement BrokerPort"])
    checks.append("broker_port")

    try:
        broker_venue = broker.venue_id
    except Exception as exc:  # noqa: BLE001 - report plugin behavior
        issues.append(f"venue_id: {_exception_text(exc)}")
    else:
        if isinstance(broker_venue, str) and broker_venue.strip().lower() == spec.venue_id:
            checks.append("venue_id")
        else:
            issues.append(f"venue_id: spec={spec.venue_id!r}, broker={broker_venue!r}")

    _check_lifecycle_call("connect", broker, checks, issues)
    _check_lifecycle_call("health", broker, checks, issues)

    if "market_data" in spec.capabilities:
        _check_market_data(broker, checks, issues)
    if "account_read" in spec.capabilities:
        _check_account_reads(broker, checks, issues)

    _check_lifecycle_call("close", broker, checks, issues)
    _check_registry_wrapper(spec, broker, mode, checks, issues)
    return _report(checks, issues)


def _check_lifecycle_call(
    name: str,
    broker: BrokerPort,
    checks: list[str],
    issues: list[str],
) -> None:
    try:
        operation = getattr(broker, name)
    except Exception as exc:  # noqa: BLE001 - report plugin behavior
        issues.append(f"lifecycle.{name}: {_exception_text(exc)}")
        return
    try:
        result = operation()
    except Exception as exc:  # noqa: BLE001 - report plugin behavior
        issues.append(f"lifecycle.{name}: {_exception_text(exc)}")
        return
    if not isinstance(result, dict):
        issues.append(f"lifecycle.{name}: expected dict, got {type(result).__name__}")
        return
    checks.append(f"lifecycle.{name}")


def _check_market_data(
    broker: BrokerPort,
    checks: list[str],
    issues: list[str],
) -> None:
    try:
        instruments = broker.list_instruments()
    except Exception as exc:  # noqa: BLE001 - report plugin behavior
        issues.append(f"market_data.instruments: {_exception_text(exc)}")
        return
    if not isinstance(instruments, list) or any(
        not isinstance(item, BrokerInstrument) for item in instruments
    ):
        issues.append("market_data.instruments: expected list[BrokerInstrument]")
        return
    if not instruments:
        issues.append(
            "market_data.instruments: offline fixture must expose at least one instrument"
        )
        return
    if any(
        not item.symbol
        or not all(
            isinstance(value, str)
            for value in (item.symbol, item.description, item.currency, item.status)
        )
        for item in instruments
    ):
        issues.append("market_data.instruments: invalid BrokerInstrument fields")
        return
    checks.append("market_data.instruments")

    symbol = instruments[0].symbol
    try:
        snapshot = broker.get_snapshot(symbol)
    except Exception as exc:  # noqa: BLE001 - report plugin behavior
        issues.append(f"market_data.snapshot: {_exception_text(exc)}")
        return
    if not isinstance(snapshot, BrokerSnapshot):
        issues.append("market_data.snapshot: expected BrokerSnapshot")
        return
    if snapshot.symbol != symbol:
        issues.append(
            f"market_data.snapshot: requested {symbol!r}, returned {snapshot.symbol!r}"
        )
        return
    snapshot_valid = True
    for field_name in ("bid", "ask", "last"):
        if not _is_finite_decimal(getattr(snapshot, field_name)):
            issues.append(f"market_data.snapshot.{field_name}: expected finite Decimal")
            snapshot_valid = False
    if (
        not isinstance(snapshot.ts, datetime)
        or snapshot.ts.tzinfo is None
        or snapshot.ts.utcoffset() is None
    ):
        issues.append("market_data.snapshot.ts: expected timezone-aware datetime")
        snapshot_valid = False
    if snapshot_valid:
        checks.append("market_data.snapshot")


def _check_account_reads(
    broker: BrokerPort,
    checks: list[str],
    issues: list[str],
) -> None:
    try:
        account = broker.get_account()
    except Exception as exc:  # noqa: BLE001 - report plugin behavior
        issues.append(f"account_read.account: {_exception_text(exc)}")
    else:
        _validate_account(account, checks, issues)

    try:
        positions = broker.get_positions()
    except Exception as exc:  # noqa: BLE001 - report plugin behavior
        issues.append(f"account_read.positions: {_exception_text(exc)}")
        return
    if not isinstance(positions, list) or any(
        not isinstance(position, BrokerPosition) for position in positions
    ):
        issues.append("account_read.positions: expected list[BrokerPosition]")
        return
    for position in positions:
        if (
            not isinstance(position.symbol, str)
            or not position.symbol
            or not _is_finite_decimal(position.quantity)
            or (
                position.avg_price is not None
                and not _is_finite_decimal(position.avg_price)
            )
        ):
            issues.append("account_read.positions: invalid position DTO/Decimal")
            return
    checks.append("account_read.positions")


def _validate_account(
    account: object,
    checks: list[str],
    issues: list[str],
) -> None:
    if not isinstance(account, BrokerAccount):
        issues.append("account_read.account: expected BrokerAccount")
        return
    if (
        not isinstance(account.currency, str)
        or not account.currency
        or not _is_finite_decimal(account.cash)
        or (account.equity is not None and not _is_finite_decimal(account.equity))
    ):
        issues.append("account_read.account: invalid account DTO/Decimal")
        return
    checks.append("account_read.account")


def _check_registry_wrapper(
    spec: BrokerPluginSpec,
    broker: BrokerPort,
    mode: OperatingMode,
    checks: list[str],
    issues: list[str],
) -> None:
    registry = BrokerRegistry()

    def cached_factory(factory_mode: OperatingMode) -> BrokerPort:
        del factory_mode
        return broker

    registry.register(spec.venue_id, cached_factory, from_plugin=True)
    try:
        wrapped = registry.create(spec.venue_id, mode)
    except Exception as exc:  # noqa: BLE001 - turn integration failure into report
        issues.append(f"registry.wrapper: {_exception_text(exc)}")
        return
    if not isinstance(wrapped, ReadOnlyBrokerPort):
        issues.append("registry.wrapper: external plugin is not wrapped read-only")
        return
    checks.append("registry.wrapper")

    blocked = 0
    try:
        wrapped.submit(cast(OrderIntent, object()))
    except ValidationError:
        blocked += 1
    except Exception as exc:  # noqa: BLE001 - report wrong failure mode
        issues.append(f"registry.wrapper.submit: {_exception_text(exc)}")
    else:
        issues.append("registry.wrapper.submit: execution was not blocked")
    try:
        wrapped.cancel("contract-v1-probe")
    except ValidationError:
        blocked += 1
    except Exception as exc:  # noqa: BLE001 - report wrong failure mode
        issues.append(f"registry.wrapper.cancel: {_exception_text(exc)}")
    else:
        issues.append("registry.wrapper.cancel: execution was not blocked")
    if blocked == 2:
        checks.append("registry.execution_blocked")


def _is_finite_decimal(value: object) -> bool:
    return isinstance(value, Decimal) and value.is_finite()


def _exception_text(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _report(checks: list[str], issues: list[str]) -> BrokerContractReport:
    return BrokerContractReport(
        passed=not issues,
        checks=tuple(checks),
        issues=tuple(issues),
    )
