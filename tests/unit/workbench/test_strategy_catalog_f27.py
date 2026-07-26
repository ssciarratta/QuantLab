"""Fase 27 — catálogo estrategias: smoke paper step + lab backtest sin LIVE."""

from __future__ import annotations

import http.client
import json
from datetime import UTC, datetime
from decimal import Decimal
from http.server import ThreadingHTTPServer
from typing import Any

import pytest

from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.orders import OrderIntent
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.lab_services import lab_strategies, run_lab_backtest
from quantlab.workbench.paper_session import PaperSessionConfig, PaperSessionRunner
from quantlab.workbench.risk import PaperRiskLimits
from quantlab.workbench.strategy_catalog import (
    CANONICAL_STRATEGY_IDS,
    build_strategy,
    list_strategy_catalog,
    normalize_strategy_id,
)


class _MdStub:
    def __init__(self, symbol: str = "TEST", last: str = "100") -> None:
        self.symbol = symbol
        self.submit_calls = 0
        self._last = Decimal(last)
        self._snap = BrokerSnapshot(
            symbol=symbol,
            bid=self._last - Decimal("1"),
            ask=self._last + Decimal("1"),
            last=self._last,
            ts=datetime(2024, 6, 1, 12, 0, tzinfo=UTC),
        )

    @property
    def venue_id(self) -> str:
        return "md-stub"

    def connect(self) -> dict[str, object]:
        return {"ok": True}

    def close(self) -> dict[str, object]:
        return {"ok": True}

    def health(self) -> dict[str, object]:
        return {"ok": True}

    def list_instruments(self) -> list[BrokerInstrument]:
        return [
            BrokerInstrument(
                symbol=self.symbol,
                description="t",
                currency="USD",
                status="ACTIVE",
            )
        ]

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        return self._snap

    def get_account(self) -> BrokerAccount:
        return BrokerAccount(cash=Decimal("1"), currency="USD")

    def get_positions(self) -> list[BrokerPosition]:
        return []

    def submit(self, intent: OrderIntent) -> BrokerAck:
        self.submit_calls += 1
        raise AssertionError("must never call md submit")

    def cancel(self, order_id: str) -> BrokerAck:
        raise AssertionError("must never call md cancel")


def _runner() -> PaperSessionRunner:
    md = _MdStub()
    book = PaperBook(initial_cash=Decimal("100000"))
    broker = PaperBroker(md, book=book)
    return PaperSessionRunner(broker, PaperRiskLimits(), book)


@pytest.mark.parametrize("strategy_id", CANONICAL_STRATEGY_IDS)
def test_catalog_build_and_normalize(strategy_id: str) -> None:
    assert LIVE_BLOCKED is True
    assert normalize_strategy_id(strategy_id) == strategy_id
    strat = build_strategy(strategy_id)
    assert strat.get_parameters()
    strat.reset()


def test_aliases() -> None:
    assert normalize_strategy_id("simple_momentum") == "momentum"
    assert normalize_strategy_id("as") == "avellaneda_stoikov"
    assert normalize_strategy_id("inv_mm") == "inventory_mm"
    with pytest.raises(ValidationError):
        normalize_strategy_id("nope")


def test_list_catalog_has_mm_and_momentum_tags() -> None:
    cats = list_strategy_catalog()
    ids = {c["id"] for c in cats}
    assert ids == set(CANONICAL_STRATEGY_IDS)
    by_id = {c["id"]: c for c in cats}
    assert "mm" in by_id["inventory_mm"]["tags"]
    assert "mm" in by_id["avellaneda_stoikov"]["tags"]
    assert "momentum" in by_id["momentum"]["tags"]
    assert "default_params" in by_id["inventory_mm"]
    assert "default_params" in by_id["avellaneda_stoikov"]


@pytest.mark.parametrize("strategy_id", CANONICAL_STRATEGY_IDS)
def test_paper_session_step_smoke(strategy_id: str) -> None:
    assert LIVE_BLOCKED is True
    runner = _runner()
    runner.start(PaperSessionConfig(strategy_id=strategy_id, symbol="TEST", max_steps=3))
    summary = runner.step()
    assert summary["ok"] is True
    assert summary["strategy_id"] == strategy_id
    assert summary["live_blocked"] is True
    assert summary["live_routing"] is False
    assert isinstance(summary["intents"], list)
    assert isinstance(summary["actions"], list)
    runner.stop()


@pytest.mark.parametrize("strategy_id", CANONICAL_STRATEGY_IDS)
def test_lab_backtest_smoke(strategy_id: str) -> None:
    assert LIVE_BLOCKED is True
    result = run_lab_backtest(strategy_id=strategy_id, n_bars=12)
    assert result["ok"] is True
    assert result["strategy_id"] == strategy_id
    assert result["live_blocked"] is True
    assert result["live_routing"] is False
    assert "metrics" in result


def test_lab_strategies_endpoint_payload() -> None:
    body = lab_strategies()
    assert body["ok"] is True
    assert body["live_blocked"] is True
    assert set(body["ids"]) == set(CANONICAL_STRATEGY_IDS)
    assert len(body["strategies"]) == len(CANONICAL_STRATEGY_IDS)


def _get(server: ThreadingHTTPServer, path: str) -> tuple[int, dict[str, Any]]:
    host, port = server.server_address[:2]
    assert isinstance(host, str) and isinstance(port, int)
    conn = http.client.HTTPConnection(host, port, timeout=30)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return resp.status, body


def test_api_lab_strategies(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/strategies")
    assert status == 200
    assert body["ok"] is True
    assert "inventory_mm" in body["ids"]
    assert "avellaneda_stoikov" in body["ids"]
    assert body["live_routing"] is False


def test_api_capabilities_includes_catalog(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    server, _ = workbench_server
    status, body = _get(server, "/api/lab/capabilities")
    assert status == 200
    assert "inventory_mm" in body["strategies"]
    assert "avellaneda_stoikov" in body["strategies"]
    assert any(s["id"] == "inventory_mm" for s in body["strategy_catalog"])
    assert any(f["id"] == "strategies" for f in body["features"])
