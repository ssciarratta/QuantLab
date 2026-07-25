"""Avellaneda–Stoikov market making (Fase 14 residual) — MVP simulado.

Referencia (simplificada):
  reservation r = mid - q * γ * σ² * τ
  half-spread δ ≈ γ * σ² * τ + (1/γ) * ln(1 + γ/k)

Emite LIMIT bid/ask alrededor de r. Sin routing LIVE.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent


class AvellanedaStoikovStrategy:
    """Cotizador AS con inventario q y parámetros γ, σ, k, T."""

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        self._parameters = dict(parameters or {})
        self._quote_ids: list[str] = []
        self._n = 0
        self._t0_events = 0

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        self._n += 1
        if self._t0_events == 0:
            self._t0_events = 1
        bid_s = context.parameters.get("best_bid")
        ask_s = context.parameters.get("best_ask")
        if bid_s is None or ask_s is None:
            return self._noop(event.instrument_id, "noop-book")

        mid = (Decimal(str(bid_s)) + Decimal(str(ask_s))) / Decimal("2")
        q = Decimal(str(context.parameters.get("inventory", "0")))
        gamma = float(self._parameters.get("gamma", 0.1))
        sigma = float(self._parameters.get("sigma", 0.02))
        kappa = float(self._parameters.get("kappa", 1.5))
        horizon = float(self._parameters.get("horizon_events", 100))
        qty = Decimal(str(self._parameters.get("quantity", "1")))
        max_pos = Decimal(str(self._parameters.get("max_pos", "10")))

        if gamma <= 0 or sigma < 0 or kappa <= 0 or horizon <= 0:
            return self._noop(event.instrument_id, "noop-params")

        # Tiempo restante normalizado τ ∈ (0, 1]
        tau = max(1.0 - (self._n / horizon), 1e-6)
        sigma2 = sigma * sigma
        reservation = float(mid) - float(q) * gamma * sigma2 * tau
        # δ óptimo (mitad del spread AS)
        try:
            delta = gamma * sigma2 * tau + (1.0 / gamma) * math.log(1.0 + gamma / kappa)
        except ValueError:
            return self._noop(event.instrument_id, "noop-delta")
        if delta <= 0:
            return self._noop(event.instrument_id, "noop-delta2")

        bid_px = Decimal(str(reservation - delta))
        ask_px = Decimal(str(reservation + delta))
        if bid_px <= 0 or ask_px <= bid_px:
            return self._noop(event.instrument_id, "noop-px")

        intents: list[OrderIntent] = []
        for qid in self._quote_ids:
            intents.append(
                OrderIntent(
                    intent_id=f"cancel-{qid}",
                    intent_type=IntentType.CANCEL_ORDER,
                    instrument_id=event.instrument_id,
                    replace_target_id=qid,
                )
            )
        self._quote_ids = []

        if q < max_pos:
            bid_id = f"as-bid-{self._n}"
            self._quote_ids.append(bid_id)
            intents.append(
                OrderIntent(
                    intent_id=bid_id,
                    intent_type=IntentType.PLACE_ORDER,
                    instrument_id=event.instrument_id,
                    side=OrderSide.BUY,
                    quantity=qty,
                    price=bid_px.quantize(Decimal("0.00000001")),
                    order_type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                )
            )
        if q > 0:
            ask_id = f"as-ask-{self._n}"
            self._quote_ids.append(ask_id)
            intents.append(
                OrderIntent(
                    intent_id=ask_id,
                    intent_type=IntentType.PLACE_ORDER,
                    instrument_id=event.instrument_id,
                    side=OrderSide.SELL,
                    quantity=min(qty, q),
                    price=ask_px.quantize(Decimal("0.00000001")),
                    order_type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                )
            )
        if not self._quote_ids:
            return self._noop(event.instrument_id, "noop-inv")
        return tuple(intents)

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        return ()

    def get_parameters(self) -> dict[str, Any]:
        return dict(self._parameters)

    def set_parameters(self, params: dict[str, Any]) -> None:
        self._parameters = dict(params)

    def get_state(self) -> dict[str, Any]:
        return {"quotes": list(self._quote_ids), "n": self._n}

    def reset(self) -> None:
        self._quote_ids.clear()
        self._n = 0
        self._t0_events = 0

    @staticmethod
    def _noop(instrument_id: str, tag: str) -> tuple[OrderIntent, ...]:
        return (
            OrderIntent(
                intent_id=f"as-{tag}",
                intent_type=IntentType.NO_ACTION,
                instrument_id=instrument_id,
            ),
        )


def reservation_price(
    *,
    mid: float,
    inventory: float,
    gamma: float,
    sigma: float,
    tau: float,
) -> float:
    """r(s, q, t) = s - q γ σ² (T - t) con τ = T - t."""
    return mid - inventory * gamma * (sigma**2) * tau


def optimal_half_spread(*, gamma: float, sigma: float, kappa: float, tau: float) -> float:
    """Mitad de spread óptimo AS (función pura para tests)."""
    return gamma * (sigma**2) * tau + (1.0 / gamma) * math.log(1.0 + gamma / kappa)


def quote_prices(
    *,
    mid: float,
    inventory: float,
    gamma: float = 0.1,
    sigma: float = 0.02,
    kappa: float = 1.5,
    tau: float = 1.0,
) -> tuple[Decimal, Decimal, Decimal]:
    """Retorna (reservation, bid, ask) en Decimal para microestructura L2."""
    r = reservation_price(mid=mid, inventory=inventory, gamma=gamma, sigma=sigma, tau=tau)
    delta = optimal_half_spread(gamma=gamma, sigma=sigma, kappa=kappa, tau=tau)
    bid = Decimal(str(r - delta)).quantize(Decimal("0.00000001"))
    ask = Decimal(str(r + delta)).quantize(Decimal("0.00000001"))
    return Decimal(str(r)).quantize(Decimal("0.00000001")), bid, ask
