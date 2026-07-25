"""Risk gate mínimo pre-trade."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

from quantlab.core.types.enums import IntentType
from quantlab.core.types.orders import OrderIntent
from quantlab.data.exchanges.a3.config import A3Config
from quantlab.data.exchanges.a3.kill_switch import KillSwitch


@dataclass(frozen=True, slots=True)
class TradingContext:
    environment: str
    account: str
    is_production: bool
    execution_enabled: bool
    allow_live_orders: bool
    live_env_confirmed: bool
    last_market_data_at: datetime | None
    last_price: Decimal | None
    open_client_order_ids: frozenset[str]


@dataclass(frozen=True, slots=True)
class RiskDecision:
    approved: bool
    reasons: tuple[str, ...]


class PreTradeRiskGate(Protocol):
    def evaluate(self, intent: OrderIntent, context: TradingContext) -> RiskDecision: ...


class DefaultPreTradeRiskGate:
    def __init__(self, config: A3Config, kill_switch: KillSwitch) -> None:
        self._config = config
        self._kill = kill_switch

    def evaluate(self, intent: OrderIntent, context: TradingContext) -> RiskDecision:
        reasons: list[str] = []
        if intent.intent_type is not IntentType.PLACE_ORDER:
            # cancel/replace se validan en otro camino; aquí solo place
            return RiskDecision(True, ())

        blocked, scope = self._kill.is_blocked(
            is_production=context.is_production,
            account=context.account,
            symbol=intent.instrument_id,
        )
        if blocked:
            reasons.append(f"kill_switch:{scope}")

        if not context.execution_enabled:
            reasons.append("execution.disabled")

        if context.is_production:
            if not context.allow_live_orders:
                reasons.append("allow_live_orders=false")
            if not context.live_env_confirmed:
                reasons.append("live_confirmation_missing")
            if (
                self._config.execution.account_allowlist
                and context.account not in self._config.execution.account_allowlist
            ):
                reasons.append("account_not_allowlisted")

        allow = self._config.risk.symbol_allowlist
        symbol = intent.instrument_id.removeprefix("a3:")
        if allow and symbol not in allow and intent.instrument_id not in allow:
            reasons.append("symbol_not_allowlisted")

        if intent.quantity is None:
            reasons.append("missing_quantity")
        elif intent.quantity > self._config.risk.max_order_quantity:
            reasons.append("quantity_above_max")
        elif intent.quantity <= 0:
            reasons.append("quantity_not_positive")

        if intent.price is not None and intent.price <= 0:
            reasons.append("invalid_price")

        max_notional = self._config.risk.max_notional
        px = intent.price if intent.price is not None else context.last_price
        if max_notional is not None:
            if px is None or intent.quantity is None:
                if self._config.risk.reject_if_insufficient_info:
                    reasons.append("insufficient_info_for_notional")
            elif px * intent.quantity > max_notional:
                reasons.append("notional_above_max")

        if context.last_market_data_at is None:
            if self._config.risk.reject_if_insufficient_info:
                reasons.append("no_market_data_freshness")
        else:
            age = (datetime.now(tz=UTC) - context.last_market_data_at).total_seconds()
            if age > self._config.risk.max_market_data_age_seconds:
                reasons.append("stale_market_data")

        # Duplicación básica por client id = intent_id
        if intent.intent_id in context.open_client_order_ids:
            reasons.append("duplicate_client_order_id")

        return RiskDecision(approved=not reasons, reasons=tuple(reasons))
