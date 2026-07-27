"""Market Maker simple con inventory skew (Fase 7 / 5B)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent


class InventoryMMStrategy:
    """Publica bid/ask alrededor del mid con sesgo por inventario.

    - Si skew > 0 (largo): baja bid y acerca ask (vende más agresivo)
    - Si skew < 0 (corto): sube ask y acerca bid
    """

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        self._parameters = dict(parameters or {})
        self._quote_ids: list[str] = []
        self._n = 0

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        self._n += 1
        bid_s = context.parameters.get("best_bid")
        ask_s = context.parameters.get("best_ask")
        if bid_s is None or ask_s is None:
            return (
                OrderIntent(
                    intent_id="mm-noop",
                    intent_type=IntentType.NO_ACTION,
                    instrument_id=event.instrument_id,
                ),
            )
        bid = Decimal(str(bid_s))
        ask = Decimal(str(ask_s))
        mid = (bid + ask) / 2
        # Preferir half del book inyectado (BarSyntheticBookAdapter ya escala alts).
        # half_spread absoluto (0.5) en mid ~0.5 deja bid~0.01 → nunca toca OHLC.
        book_half = (ask - bid) / 2
        half_spread = Decimal(str(self._parameters.get("half_spread", "0.5")))
        if book_half > 0 and (mid <= 0 or half_spread / mid > Decimal("0.02")):
            half_spread = book_half
        elif mid > 0 and half_spread / mid > Decimal("0.02"):
            half_spread = mid * Decimal("0.005")
        qty = Decimal(str(self._parameters.get("quantity", "1")))
        skew = Decimal(str(context.parameters.get("inventory_skew", "0")))
        # skew largo → bid más bajo, ask más bajo (vende)
        bid_px = mid - half_spread - skew * half_spread
        ask_px = mid + half_spread - skew * half_spread
        if bid_px <= 0 or ask_px <= bid_px:
            return (
                OrderIntent(
                    intent_id="mm-noop-px",
                    intent_type=IntentType.NO_ACTION,
                    instrument_id=event.instrument_id,
                ),
            )

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
        inv = Decimal(str(context.parameters.get("inventory", "0")))
        # Long-only en portfolio tracker: bid siempre (si no al máximo); ask solo con inventario
        if inv < Decimal(str(self._parameters.get("max_pos", "10"))):
            bid_id = f"mm-bid-{self._n}"
            self._quote_ids.append(bid_id)
            intents.append(
                OrderIntent(
                    intent_id=bid_id,
                    intent_type=IntentType.PLACE_ORDER,
                    instrument_id=event.instrument_id,
                    side=OrderSide.BUY,
                    quantity=qty,
                    price=bid_px,
                    order_type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                )
            )
        if inv > 0:
            ask_id = f"mm-ask-{self._n}"
            self._quote_ids.append(ask_id)
            intents.append(
                OrderIntent(
                    intent_id=ask_id,
                    intent_type=IntentType.PLACE_ORDER,
                    instrument_id=event.instrument_id,
                    side=OrderSide.SELL,
                    quantity=min(qty, inv),
                    price=ask_px,
                    order_type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                )
            )
        if not self._quote_ids:
            return (
                OrderIntent(
                    intent_id="mm-noop-inv",
                    intent_type=IntentType.NO_ACTION,
                    instrument_id=event.instrument_id,
                ),
            )
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
