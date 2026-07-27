"""Variantes MM del espectro (F115) — bar/event con book sintético en lab."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.core.contracts.strategy import StrategyContext
from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent
from quantlab.research.strategies.inventory_mm import InventoryMMStrategy


class DynamicSpreadMMStrategy(InventoryMMStrategy):
    """Inventory MM con half_spread escalado por rango reciente (proxy ATR)."""

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        super().__init__(parameters)
        self._closes: list[Decimal] = []

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        close_s = None
        if event.payload:
            close_s = event.payload.get("close")
        if close_s is not None:
            self._closes.append(Decimal(str(close_s)))
            period = int(self._parameters.get("atr_period", 10))
            base = Decimal(str(self._parameters.get("half_spread", "0.5")))
            mult = Decimal(str(self._parameters.get("vol_mult", "1")))
            if len(self._closes) >= 2:
                # True range proxy: |Δclose|
                recent = self._closes[-period:] if len(self._closes) >= period else self._closes
                diffs = [
                    abs(recent[i] - recent[i - 1]) for i in range(1, len(recent))
                ]
                if diffs:
                    atr = sum(diffs, Decimal("0")) / Decimal(len(diffs))
                    mid = self._closes[-1]
                    # base absoluto 0.5 rompe alts; anclar a bps del mid
                    if mid > 0 and base / mid > Decimal("0.02"):
                        base = mid * Decimal("0.005")
                    dyn = max(base, atr * mult)
                    # Evitar spreads absurdos vs mid
                    if mid > 0:
                        dyn = min(dyn, mid * Decimal("0.05"))
                    self._parameters = {**self._parameters, "half_spread": str(dyn)}
        return super().on_event(event, context)

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        self._closes.append(bar.close)
        return super().on_bar(bar, context)

    def reset(self) -> None:
        super().reset()
        self._closes.clear()


class MultiLevelMMStrategy:
    """MM con 2 niveles de cotización a cada lado (simulado)."""

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
                    intent_id="mlmm-noop",
                    intent_type=IntentType.NO_ACTION,
                    instrument_id=event.instrument_id,
                ),
            )
        mid = (Decimal(str(bid_s)) + Decimal(str(ask_s))) / 2
        book_half = (Decimal(str(ask_s)) - Decimal(str(bid_s))) / 2
        half = Decimal(str(self._parameters.get("half_spread", "0.5")))
        if book_half > 0 and (mid <= 0 or half / mid > Decimal("0.02")):
            half = book_half
        elif mid > 0 and half / mid > Decimal("0.02"):
            half = mid * Decimal("0.005")
        step = Decimal(str(self._parameters.get("level_step", "0.5")))
        if mid > 0 and step / mid > Decimal("0.02"):
            step = mid * Decimal("0.005")
        qty = Decimal(str(self._parameters.get("quantity", "1")))
        levels = int(self._parameters.get("levels", 2))
        levels = max(1, min(levels, 5))
        skew = Decimal(str(context.parameters.get("inventory_skew", "0")))
        inv = Decimal(str(context.parameters.get("inventory", "0")))
        max_pos = Decimal(str(self._parameters.get("max_pos", "10")))

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

        for lvl in range(levels):
            offset = half + step * Decimal(lvl)
            bid_px = mid - offset - skew * half
            ask_px = mid + offset - skew * half
            if bid_px <= 0 or ask_px <= bid_px:
                continue
            if inv < max_pos:
                bid_id = f"mlmm-bid-{self._n}-{lvl}"
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
                ask_id = f"mlmm-ask-{self._n}-{lvl}"
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
                    intent_id="mlmm-noop-flat",
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
        return {"n": self._n, "quotes": list(self._quote_ids)}

    def reset(self) -> None:
        self._quote_ids.clear()
        self._n = 0


class AdaptiveMMStrategy(DynamicSpreadMMStrategy):
    """Dynamic spread + skew extra si inventario cerca del máximo."""

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        inv = Decimal(str(context.parameters.get("inventory", "0")))
        max_pos = Decimal(str(self._parameters.get("max_pos", "10")))
        boost = Decimal(str(self._parameters.get("inventory_boost", "1.5")))
        merged = dict(context.parameters)
        if max_pos > 0 and abs(inv) >= max_pos * Decimal("0.7"):
            skew = Decimal(str(merged.get("inventory_skew", "0")))
            merged["inventory_skew"] = str(skew * boost)
            context = StrategyContext(
                clock=context.clock,
                portfolio_state=context.portfolio_state,
                parameters=merged,
            )
        return super().on_event(event, context)
