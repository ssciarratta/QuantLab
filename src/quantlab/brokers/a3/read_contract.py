"""Certificación read-only del market-data A3.

La lane fake es determinista/offline. La lane sandbox sólo puede usar pyRofex
en ``simulation`` con opt-in explícito y resolución sin fallback.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from time import perf_counter
from typing import Any, NoReturn

from quantlab.brokers.a3.md_backend import MD_SOURCE_ENV, resolve_a3_md_backend
from quantlab.data.exchanges.a3.client import PyRofexBackend
from quantlab.data.exchanges.a3.exceptions import A3ConfigurationError
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend
from quantlab.data.exchanges.a3.models import (
    A3AccountSummaryDTO,
    A3InstrumentDTO,
    A3MarketSnapshotDTO,
    A3OrderAckDTO,
    A3PositionDTO,
    A3TradeDTO,
)
from quantlab.data.exchanges.a3.protocols import A3Backend
from quantlab.execution.live_gate import LIVE_BLOCKED

SANDBOX_CERT_ENV = "QUANTLAB_RUN_A3_SANDBOX_CERT"
_CREDENTIAL_ENV_NAMES = (
    "QUANTLAB_A3_USER",
    "QUANTLAB_A3_PASSWORD",
    "QUANTLAB_A3_ACCOUNT",
)


class A3ReadContractStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED_NOT_REQUESTED = "SKIPPED_NOT_REQUESTED"


@dataclass(frozen=True, slots=True)
class LatencySummary:
    count: int
    min: float
    max: float
    mean: float

    @classmethod
    def from_samples(cls, samples: list[float]) -> LatencySummary:
        if not samples:
            return cls(count=0, min=0.0, max=0.0, mean=0.0)
        rounded = [round(value, 3) for value in samples]
        return cls(
            count=len(rounded),
            min=min(rounded),
            max=max(rounded),
            mean=round(sum(rounded) / len(rounded), 3),
        )

    def to_dict(self) -> dict[str, int | float]:
        return {
            "count": self.count,
            "min": self.min,
            "max": self.max,
            "mean": self.mean,
        }


@dataclass(frozen=True, slots=True)
class A3ReadContractReport:
    status: A3ReadContractStatus
    lane: str
    provider: str
    environment: str
    instruments_count: int
    snapshots_count: int
    latency_ms: LatencySummary
    live_blocked: bool
    write_calls: int
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Retorna sólo campos de evidencia permitidos, sin payloads ni identidad."""
        return {
            "status": self.status.value,
            "lane": self.lane,
            "provider": self.provider,
            "environment": self.environment,
            "instruments_count": self.instruments_count,
            "snapshots_count": self.snapshots_count,
            "latency_ms": self.latency_ms.to_dict(),
            "live_blocked": self.live_blocked,
            "write_calls": self.write_calls,
            "issues": list(self.issues),
        }


class A3ReadOnlyBackendSpy:
    """Delega lecturas y hace explotar cualquier intento de escritura."""

    def __init__(self, backend: A3Backend) -> None:
        self._backend = backend
        self.write_calls = 0

    def connect(self) -> None:
        self._backend.connect()

    def close(self) -> None:
        self._backend.close()

    def health_check(self) -> dict[str, Any]:
        return self._backend.health_check()

    def get_instruments(self) -> list[A3InstrumentDTO]:
        return self._backend.get_instruments()

    def get_instrument_details(self, symbol: str) -> A3InstrumentDTO:
        return self._backend.get_instrument_details(symbol)

    def get_market_snapshot(self, symbol: str, depth: int = 5) -> A3MarketSnapshotDTO:
        return self._backend.get_market_snapshot(symbol, depth)

    def get_historical_trades(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[A3TradeDTO]:
        return self._backend.get_historical_trades(symbol, start, end)

    def get_order_status(self, order_id: str) -> A3OrderAckDTO:
        return self._backend.get_order_status(order_id)

    def get_orders(self) -> list[A3OrderAckDTO]:
        return self._backend.get_orders()

    def get_account_summary(self) -> A3AccountSummaryDTO:
        return self._backend.get_account_summary()

    def get_positions(self) -> list[A3PositionDTO]:
        return self._backend.get_positions()

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        size: str,
        order_type: str,
        price: str | None,
        client_order_id: str,
    ) -> NoReturn:
        del symbol, side, size, order_type, price, client_order_id
        self.write_calls += 1
        raise RuntimeError("A3 certification write bomb: place_order")

    def cancel_order(self, order_id: str) -> NoReturn:
        del order_id
        self.write_calls += 1
        raise RuntimeError("A3 certification write bomb: cancel_order")


def _measure(samples: list[float], operation: Any) -> Any:
    started = perf_counter()
    try:
        return operation()
    finally:
        samples.append((perf_counter() - started) * 1000.0)


def _require_finite(value: Decimal | None, *, optional: bool = False) -> None:
    if value is None:
        if optional:
            return
        raise ValueError("missing_decimal")
    if not value.is_finite():
        raise ValueError("non_finite_decimal")


def _validate_instrument(instrument: A3InstrumentDTO) -> None:
    if not isinstance(instrument, A3InstrumentDTO) or not instrument.symbol.strip():
        raise ValueError("invalid_instrument")
    for value in (
        instrument.tick_size,
        instrument.contract_multiplier,
        instrument.lot_size,
    ):
        _require_finite(value, optional=True)


def _validate_snapshot(snapshot: A3MarketSnapshotDTO, symbol: str) -> None:
    if not isinstance(snapshot, A3MarketSnapshotDTO) or snapshot.symbol != symbol:
        raise ValueError("invalid_snapshot")
    if snapshot.timestamp.tzinfo is None or snapshot.timestamp.utcoffset() is None:
        raise ValueError("naive_snapshot_timestamp")
    for level in (*snapshot.bids, *snapshot.offers):
        _require_finite(level.price)
        _require_finite(level.size)
    for value in (snapshot.last_price, snapshot.last_size, snapshot.open_interest):
        _require_finite(value, optional=True)


def _validate_account(account: A3AccountSummaryDTO) -> None:
    if not isinstance(account, A3AccountSummaryDTO):
        raise ValueError("invalid_account")
    _require_finite(account.available, optional=True)


def _validate_positions(positions: list[A3PositionDTO]) -> None:
    for position in positions:
        if not isinstance(position, A3PositionDTO) or not position.symbol.strip():
            raise ValueError("invalid_position")
        _require_finite(position.quantity)
        _require_finite(position.avg_price, optional=True)


def _empty_report(
    *,
    status: A3ReadContractStatus,
    lane: str,
    provider: str,
    environment: str,
    issue: str,
) -> A3ReadContractReport:
    return A3ReadContractReport(
        status=status,
        lane=lane,
        provider=provider,
        environment=environment,
        instruments_count=0,
        snapshots_count=0,
        latency_ms=LatencySummary.from_samples([]),
        live_blocked=LIVE_BLOCKED,
        write_calls=0,
        issues=(issue,),
    )


def _run_contract(
    backend: A3Backend,
    *,
    lane: str,
    provider: str,
    environment: str,
    include_account: bool,
) -> A3ReadContractReport:
    spy = A3ReadOnlyBackendSpy(backend)
    samples: list[float] = []
    issues: list[str] = []
    instruments_count = 0
    snapshots_count = 0
    stage = "connect"

    try:
        _measure(samples, spy.connect)
        stage = "health"
        health = _measure(samples, spy.health_check)
        if not isinstance(health, dict) or health.get("ok") is not True:
            raise ValueError("unhealthy")

        stage = "instruments"
        instruments = _measure(samples, spy.get_instruments)
        if not isinstance(instruments, list) or not instruments:
            raise ValueError("empty_instruments")
        for instrument in instruments:
            _validate_instrument(instrument)
        instruments_count = len(instruments)

        stage = "snapshot"
        symbol = instruments[0].symbol
        snapshot = _measure(samples, lambda: spy.get_market_snapshot(symbol))
        _validate_snapshot(snapshot, symbol)
        snapshots_count = 1

        if include_account:
            stage = "account"
            account = _measure(samples, spy.get_account_summary)
            _validate_account(account)
            stage = "positions"
            positions = _measure(samples, spy.get_positions)
            if not isinstance(positions, list):
                raise ValueError("invalid_positions")
            _validate_positions(positions)
    except Exception:  # noqa: BLE001 — resultado cerrado y saneado
        issues.append(f"{stage}_failed")
    finally:
        try:
            _measure(samples, spy.close)
        except Exception:  # noqa: BLE001 — no filtrar texto del proveedor
            issues.append("close_failed")

    if spy.write_calls:
        issues.append("write_call_detected")
    if LIVE_BLOCKED is not True:
        issues.append("live_not_blocked")

    return A3ReadContractReport(
        status=A3ReadContractStatus.FAIL if issues else A3ReadContractStatus.PASS,
        lane=lane,
        provider=provider,
        environment=environment,
        instruments_count=instruments_count,
        snapshots_count=snapshots_count,
        latency_ms=LatencySummary.from_samples(samples),
        live_blocked=LIVE_BLOCKED,
        write_calls=spy.write_calls,
        issues=tuple(issues),
    )


def run_fake_read_contract(
    *, backend: A3Backend | None = None, include_account: bool = True
) -> A3ReadContractReport:
    """Ejecuta la lane CI/offline con fake inyectable para tests adversariales."""
    return _run_contract(
        backend or FakeA3Backend(),
        lane="fake",
        provider="a3-fake",
        environment="offline",
        include_account=include_account,
    )


def run_sandbox_read_contract_from_env(
    *, include_account: bool = True
) -> A3ReadContractReport:
    """Ejecuta pyRofex simulation sólo bajo doble opt-in y sin fallback."""
    raw_environment = os.environ.get("QUANTLAB_A3_ENVIRONMENT", "simulation").strip().lower()
    environment = raw_environment if raw_environment in {"simulation", "production"} else "invalid"

    if os.environ.get(SANDBOX_CERT_ENV, "").strip() != "1":
        return _empty_report(
            status=A3ReadContractStatus.SKIPPED_NOT_REQUESTED,
            lane="sandbox",
            provider="pyRofex",
            environment=environment,
            issue="sandbox_not_requested",
        )
    if os.environ.get("QUANTLAB_A3_MD_READONLY", "").strip() != "1":
        return _empty_report(
            status=A3ReadContractStatus.FAIL,
            lane="sandbox",
            provider="pyRofex",
            environment=environment,
            issue="readonly_opt_in_missing",
        )
    if environment != "simulation":
        return _empty_report(
            status=A3ReadContractStatus.FAIL,
            lane="sandbox",
            provider="pyRofex",
            environment=environment,
            issue="simulation_required",
        )
    if not all(os.environ.get(name, "").strip() for name in _CREDENTIAL_ENV_NAMES):
        return _empty_report(
            status=A3ReadContractStatus.FAIL,
            lane="sandbox",
            provider="pyRofex",
            environment=environment,
            issue="credentials_missing",
        )

    try:
        backend, detail = resolve_a3_md_backend(MD_SOURCE_ENV, allow_fallback=False)
    except A3ConfigurationError:
        return _empty_report(
            status=A3ReadContractStatus.FAIL,
            lane="sandbox",
            provider="pyRofex",
            environment=environment,
            issue="strict_backend_unavailable",
        )
    if (
        not isinstance(backend, PyRofexBackend)
        or detail.get("fallback")
        or detail.get("md_source") != MD_SOURCE_ENV
    ):
        return _empty_report(
            status=A3ReadContractStatus.FAIL,
            lane="sandbox",
            provider="pyRofex",
            environment=environment,
            issue="strict_backend_violation",
        )
    return _run_contract(
        backend,
        lane="sandbox",
        provider="pyRofex",
        environment=environment,
        include_account=include_account,
    )
