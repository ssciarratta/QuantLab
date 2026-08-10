"""A3BrokerPort — MD/cuenta vía fake o env read-only; execution plane fail-closed."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.brokers.a3.md_backend import (
    MD_SOURCE_FAKE,
    VALID_MD_SOURCES,
    resolve_a3_md_backend,
)
from quantlab.brokers.mode import ModeGuard, OperatingMode
from quantlab.brokers.types import (
    BrokerAccount,
    BrokerAck,
    BrokerInstrument,
    BrokerPosition,
    BrokerSnapshot,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.orders import OrderIntent
from quantlab.data.exchanges.a3.protocols import A3Backend
from quantlab.execution.live_gate import assert_live_routing_blocked


class A3BrokerPort:
    """Puerto A3 orientado a market data / account read.

    ``md_source``:
      - ``fake`` (default CI): FakeA3Backend
      - ``env``: intenta PyRofexBackend solo si ``QUANTLAB_A3_MD_READONLY=1``
        y hay ``QUANTLAB_A3_*``; si no, fallback fake + detail en health.

    ``submit`` / ``cancel`` SIEMPRE llaman ``assert_live_routing_blocked()``
    (incluso en PAPER). Para fills PAPER usar ``PaperBroker`` envolviendo este port.
    """

    def __init__(
        self,
        backend: A3Backend | None = None,
        mode: OperatingMode = OperatingMode.TESTER,
        *,
        md_source: str = MD_SOURCE_FAKE,
    ) -> None:
        ModeGuard.validate_boot(mode)
        self._mode = mode
        source = (md_source or MD_SOURCE_FAKE).strip().lower()
        if source not in VALID_MD_SOURCES:
            raise ValidationError(f"md_source inválido: {md_source!r} (fake|env)")
        self._md_meta: dict[str, Any]
        if backend is not None:
            self._backend = backend
            self._md_meta = {
                "md_source_requested": source,
                "md_source": source,
                "md_provider": "a3-injected",
                "fallback": False,
                "fallback_reason": "",
            }
        else:
            self._backend, self._md_meta = resolve_a3_md_backend(source)

    @property
    def venue_id(self) -> str:
        return "a3"

    @property
    def mode(self) -> OperatingMode:
        return self._mode

    @property
    def md_provider(self) -> str:
        return str(self._md_meta.get("md_provider") or "a3-fake")

    @property
    def md_source(self) -> str:
        return str(self._md_meta.get("md_source") or MD_SOURCE_FAKE)

    def connect(self) -> dict[str, object]:
        self._backend.connect()
        out: dict[str, object] = {
            "ok": True,
            "venue": self.venue_id,
            "mode": self._mode.value,
            "md_provider": self.md_provider,
            "md_source": self.md_source,
        }
        if self._md_meta.get("fallback"):
            out["md_fallback"] = True
            out["md_fallback_reason"] = self._md_meta.get("fallback_reason") or ""
        return out

    def close(self) -> dict[str, object]:
        self._backend.close()
        return {"ok": True, "venue": self.venue_id, "closed": True}

    def health(self) -> dict[str, object]:
        raw: dict[str, Any] = dict(self._backend.health_check())
        raw["venue"] = self.venue_id
        raw["mode"] = self._mode.value
        raw["md_only"] = True
        raw["md_provider"] = self.md_provider
        raw["md_source"] = self.md_source
        raw["md_source_requested"] = self._md_meta.get("md_source_requested")
        if self._md_meta.get("fallback"):
            raw["md_fallback"] = True
            raw["md_fallback_reason"] = self._md_meta.get("fallback_reason") or ""
        return raw

    def list_instruments(self) -> list[BrokerInstrument]:
        out: list[BrokerInstrument] = []
        for inst in self._backend.get_instruments():
            desc = inst.description or ""
            if inst.maturity:
                desc = (
                    f"{desc} · vence {inst.maturity} · margen+dif.diarias"
                    if desc
                    else f"vence {inst.maturity} · margen+dif.diarias"
                )
            out.append(
                BrokerInstrument(
                    symbol=inst.symbol,
                    description=desc,
                    currency=inst.currency or "",
                    status=inst.status or "UNKNOWN",
                )
            )
        return out

    def get_snapshot(self, symbol: str) -> BrokerSnapshot:
        snap = self._backend.get_market_snapshot(symbol)
        bid = snap.bids[0].price if snap.bids else Decimal("0")
        ask = snap.offers[0].price if snap.offers else Decimal("0")
        last = snap.last_price if snap.last_price is not None else Decimal("0")
        return BrokerSnapshot(
            symbol=snap.symbol,
            bid=bid,
            ask=ask,
            last=last,
            ts=snap.timestamp,
        )

    def get_account(self) -> BrokerAccount:
        acct = self._backend.get_account_summary()
        cash = acct.available if acct.available is not None else Decimal("0")
        return BrokerAccount(
            cash=cash,
            currency=acct.currency or "",
            equity=None,
        )

    def get_positions(self) -> list[BrokerPosition]:
        return [
            BrokerPosition(
                symbol=p.symbol,
                quantity=p.quantity,
                avg_price=p.avg_price,
            )
            for p in self._backend.get_positions()
        ]

    def submit(self, intent: OrderIntent) -> BrokerAck:
        # MD-only execution plane: siempre fail-closed (PAPER → PaperBroker).
        assert_live_routing_blocked()
        raise ValidationError("A3BrokerPort is MD-only; use PaperBroker for PAPER fills")

    def cancel(self, order_id: str) -> BrokerAck:
        assert_live_routing_blocked()
        raise ValidationError("A3BrokerPort is MD-only; use PaperBroker for PAPER cancels")
