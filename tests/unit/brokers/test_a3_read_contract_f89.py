"""Contrato de certificación A3 MD read-only (Fase 89), siempre offline."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from typing import Any
from unittest.mock import patch

import pytest

from quantlab.brokers.a3.md_backend import MD_SOURCE_ENV, resolve_a3_md_backend
from quantlab.brokers.a3.read_contract import (
    SANDBOX_CERT_ENV,
    A3ReadContractStatus,
    A3ReadOnlyBackendSpy,
    run_fake_read_contract,
    run_sandbox_read_contract_from_env,
)
from quantlab.data.exchanges.a3.exceptions import A3ConfigurationError
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend

_A3_ENV = (
    SANDBOX_CERT_ENV,
    "QUANTLAB_A3_MD_READONLY",
    "QUANTLAB_A3_ENVIRONMENT",
    "QUANTLAB_A3_USER",
    "QUANTLAB_A3_PASSWORD",
    "QUANTLAB_A3_ACCOUNT",
    "QUANTLAB_A3_TOKEN",
)


def _clear_a3_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _A3_ENV:
        monkeypatch.delenv(name, raising=False)


def _enable_sandbox(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SANDBOX_CERT_ENV, "1")
    monkeypatch.setenv("QUANTLAB_A3_MD_READONLY", "1")
    monkeypatch.setenv("QUANTLAB_A3_ENVIRONMENT", "simulation")
    monkeypatch.setenv("QUANTLAB_A3_USER", "user-secret")
    monkeypatch.setenv("QUANTLAB_A3_PASSWORD", "password-secret")
    monkeypatch.setenv("QUANTLAB_A3_ACCOUNT", "account-secret")


def test_fake_contract_passes_and_report_is_frozen() -> None:
    report = run_fake_read_contract()

    assert report.status is A3ReadContractStatus.PASS
    assert report.lane == "fake"
    assert report.instruments_count == 8  # FakeA3Backend: DLR×2 + granos curados
    assert report.snapshots_count == 1
    assert report.write_calls == 0
    assert report.live_blocked is True
    assert report.latency_ms.count == 7
    with pytest.raises(FrozenInstanceError):
        report.write_calls = 1  # type: ignore[misc]


def test_write_bomb_never_delegates() -> None:
    backend = FakeA3Backend()
    spy = A3ReadOnlyBackendSpy(backend)

    with pytest.raises(RuntimeError, match="write bomb"):
        spy.place_order(
            symbol="DLR/DIC24",
            side="buy",
            size="1",
            order_type="market",
            price=None,
            client_order_id="forbidden",
        )
    with pytest.raises(RuntimeError, match="write bomb"):
        spy.cancel_order("forbidden")

    assert spy.write_calls == 2
    assert backend.placed == []
    assert backend.orders == {}


def test_sandbox_not_requested_is_skip_not_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_a3_env(monkeypatch)

    report = run_sandbox_read_contract_from_env()

    assert report.status is A3ReadContractStatus.SKIPPED_NOT_REQUESTED
    assert report.issues == ("sandbox_not_requested",)


def test_production_rejected_before_backend_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_sandbox(monkeypatch)
    monkeypatch.setenv("QUANTLAB_A3_ENVIRONMENT", "production")

    with patch(
        "quantlab.brokers.a3.read_contract.resolve_a3_md_backend"
    ) as resolver:
        report = run_sandbox_read_contract_from_env()

    assert report.status is A3ReadContractStatus.FAIL
    assert report.issues == ("simulation_required",)
    resolver.assert_not_called()


def test_missing_credentials_fails_before_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_sandbox(monkeypatch)
    monkeypatch.delenv("QUANTLAB_A3_PASSWORD")

    with patch(
        "quantlab.brokers.a3.read_contract.resolve_a3_md_backend"
    ) as resolver:
        report = run_sandbox_read_contract_from_env()

    assert report.status is A3ReadContractStatus.FAIL
    assert report.issues == ("credentials_missing",)
    resolver.assert_not_called()


def test_strict_resolver_never_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_a3_env(monkeypatch)
    monkeypatch.setenv("QUANTLAB_A3_MD_READONLY", "1")

    with pytest.raises(A3ConfigurationError, match="no disponible"):
        resolve_a3_md_backend(MD_SOURCE_ENV, allow_fallback=False)


def test_sandbox_uses_strict_resolver_and_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_sandbox(monkeypatch)

    class TrackingBackend(FakeA3Backend):
        close_calls = 0

        def close(self) -> None:
            self.close_calls += 1
            super().close()

    backend = TrackingBackend()
    with (
        patch("quantlab.brokers.a3.read_contract.PyRofexBackend", TrackingBackend),
        patch(
            "quantlab.brokers.a3.read_contract.resolve_a3_md_backend",
            return_value=(
                backend,
                {"fallback": False, "md_source": "env", "md_provider": "a3-env-readonly"},
            ),
        ) as resolver,
    ):
        report = run_sandbox_read_contract_from_env()

    assert report.status is A3ReadContractStatus.PASS
    assert report.write_calls == 0
    assert backend.close_calls == 1
    resolver.assert_called_once_with(MD_SOURCE_ENV, allow_fallback=False)


def test_sandbox_rejects_fake_even_if_metadata_claims_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_sandbox(monkeypatch)
    with patch(
        "quantlab.brokers.a3.read_contract.resolve_a3_md_backend",
        return_value=(
            FakeA3Backend(),
            {"fallback": False, "md_source": "env", "md_provider": "a3-env-readonly"},
        ),
    ):
        report = run_sandbox_read_contract_from_env()

    assert report.status is A3ReadContractStatus.FAIL
    assert report.issues == ("strict_backend_violation",)


def test_close_runs_after_read_failure_and_error_text_is_redacted() -> None:
    secret = "password=hunter2 account=ACC-123 raw_payload"

    class FailingBackend(FakeA3Backend):
        close_calls = 0

        def health_check(self) -> dict[str, Any]:
            raise RuntimeError(secret)

        def close(self) -> None:
            self.close_calls += 1
            super().close()

    backend = FailingBackend()
    report = run_fake_read_contract(backend=backend)
    serialized = json.dumps(report.to_dict()).lower()

    assert report.status is A3ReadContractStatus.FAIL
    assert report.issues == ("health_failed",)
    assert backend.close_calls == 1
    assert "hunter2" not in serialized
    assert "acc-123" not in serialized
    assert "raw_payload" not in serialized
    assert '"account"' not in serialized
    assert '"raw"' not in serialized
