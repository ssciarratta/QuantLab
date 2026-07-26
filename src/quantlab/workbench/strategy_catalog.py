"""Catálogo de estrategias usables desde workbench (paper session + lab) — F27.

Metadata (id, nombre, defaults, tags) + factory común. Sin LIVE.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from quantlab.core.contracts.strategy import Strategy, StrategyContext
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import EventType
from quantlab.core.types.market import Bar, MarketEvent
from quantlab.core.types.orders import OrderIntent
from quantlab.research.strategies.avellaneda_stoikov import AvellanedaStoikovStrategy
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.research.strategies.dummy_strategy import DummyStrategy
from quantlab.research.strategies.inventory_mm import InventoryMMStrategy
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy

# IDs canónicos expuestos en UI / API (aliases se normalizan a estos).
CANONICAL_STRATEGY_IDS: tuple[str, ...] = (
    "dummy",
    "buy_once",
    "momentum",
    "inventory_mm",
    "avellaneda_stoikov",
)

# Compat: simple_momentum → momentum; as → avellaneda_stoikov
_ALIASES: dict[str, str] = {
    "simple_momentum": "momentum",
    "as": "avellaneda_stoikov",
    "avellaneda": "avellaneda_stoikov",
    "inv_mm": "inventory_mm",
    "inventory": "inventory_mm",
}


@dataclass(frozen=True, slots=True)
class StrategyMeta:
    """Metadata de una estrategia del catálogo workbench."""

    id: str
    name: str
    tags: tuple[str, ...]
    default_params: Mapping[str, Any]
    description: str = ""


STRATEGY_CATALOG: tuple[StrategyMeta, ...] = (
    StrategyMeta(
        id="dummy",
        name="Dummy",
        tags=("demo", "momentum"),
        default_params={"quantity": "0.01", "price": "100.0"},
        description="PLACE fijo en cada barra (demo).",
    ),
    StrategyMeta(
        id="buy_once",
        name="Buy Once",
        tags=("demo", "momentum"),
        default_params={"quantity": "1"},
        description="Compra una sola vez en la primera barra.",
    ),
    StrategyMeta(
        id="momentum",
        name="Simple Momentum",
        tags=("momentum",),
        default_params={"quantity": "1", "lookback": 3},
        description="Compra/vende según N closes consecutivos.",
    ),
    StrategyMeta(
        id="inventory_mm",
        name="Inventory MM",
        tags=("mm",),
        default_params={"quantity": "1", "half_spread": "0.5", "max_pos": "10"},
        description="Market maker con skew por inventario (bid/ask alrededor del mid).",
    ),
    StrategyMeta(
        id="avellaneda_stoikov",
        name="Avellaneda–Stoikov",
        tags=("mm",),
        default_params={
            "quantity": "1",
            "gamma": 0.1,
            "sigma": 0.02,
            "kappa": 1.5,
            "horizon_events": 100,
            "max_pos": "10",
        },
        description="Cotizador AS con reserva e inventario (MVP simulado).",
    ),
)

_BY_ID: dict[str, StrategyMeta] = {m.id: m for m in STRATEGY_CATALOG}


def normalize_strategy_id(strategy_id: str) -> str:
    """Normaliza alias → id canónico; valida existencia."""
    if not isinstance(strategy_id, str) or not strategy_id.strip():
        raise ValidationError("strategy_id requerido")
    sid = strategy_id.strip().lower()
    sid = _ALIASES.get(sid, sid)
    if sid not in _BY_ID:
        raise ValidationError(
            f"strategy_id desconocido: {strategy_id!r}; "
            f"disponibles: {', '.join(CANONICAL_STRATEGY_IDS)}"
        )
    return sid


def get_strategy_meta(strategy_id: str) -> StrategyMeta:
    return _BY_ID[normalize_strategy_id(strategy_id)]


def list_strategy_ids() -> list[str]:
    return list(CANONICAL_STRATEGY_IDS)


def list_strategy_catalog() -> list[dict[str, Any]]:
    """Lista metadata serializable (API / UI)."""
    out: list[dict[str, Any]] = []
    for m in STRATEGY_CATALOG:
        out.append(
            {
                "id": m.id,
                "name": m.name,
                "tags": list(m.tags),
                "default_params": dict(m.default_params),
                "description": m.description,
            }
        )
    return out


def merge_default_params(
    strategy_id: str, params: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Defaults del catálogo + override del caller."""
    meta = get_strategy_meta(strategy_id)
    merged = dict(meta.default_params)
    if params:
        merged.update(dict(params))
    return merged


def build_strategy(strategy_id: str, params: Mapping[str, Any] | None = None) -> Strategy:
    """Factory research strategies para paper session / lab backtest."""
    sid = normalize_strategy_id(strategy_id)
    strategy_params = merge_default_params(sid, params)
    if sid == "dummy":
        return DummyStrategy(strategy_params)
    if sid == "buy_once":
        return BuyOnceStrategy(strategy_params)
    if sid == "momentum":
        return SimpleMomentumStrategy(strategy_params)
    if sid == "inventory_mm":
        return InventoryMMStrategy(strategy_params)
    if sid == "avellaneda_stoikov":
        return AvellanedaStoikovStrategy(strategy_params)
    raise ValidationError(f"strategy_id sin factory: {sid!r}")


def is_mm_strategy(strategy_id: str) -> bool:
    meta = get_strategy_meta(strategy_id)
    return "mm" in meta.tags


class BarSyntheticBookAdapter:
    """Adapta estrategias MM al motor bar-based 5A.

    Inyecta ``best_bid`` / ``best_ask`` / ``inventory`` desde ``bar.close``
    (± half_spread) y portfolio. Sin microestructura real.
    """

    def __init__(self, inner: Strategy, *, half_spread: Decimal | None = None) -> None:
        self._inner = inner
        params = inner.get_parameters()
        if half_spread is not None:
            self._half = half_spread
        else:
            self._half = Decimal(str(params.get("half_spread", "0.5")))

    def on_event(self, event: MarketEvent, context: StrategyContext) -> tuple[OrderIntent, ...]:
        close_s = event.payload.get("close") if event.payload else None
        if close_s is None:
            return self._inner.on_event(event, context)
        close = Decimal(str(close_s))
        enriched = self._enrich(context, event.instrument_id, close)
        return self._inner.on_event(event, enriched)

    def on_bar(self, bar: Bar, context: StrategyContext) -> tuple[OrderIntent, ...]:
        enriched = self._enrich(context, bar.instrument_id, bar.close)
        intents = self._inner.on_event(
            MarketEvent(
                event_id=f"adapt-{bar.instrument_id}-{bar.timestamp_close.isoformat()}",
                event_type=EventType.BAR,
                timestamp=bar.timestamp_close,
                instrument_id=bar.instrument_id,
                payload={"timeframe": bar.timeframe, "close": str(bar.close)},
            ),
            enriched,
        )
        if intents:
            return intents
        return self._inner.on_bar(bar, enriched)

    def get_parameters(self) -> dict[str, Any]:
        return self._inner.get_parameters()

    def set_parameters(self, params: dict[str, Any]) -> None:
        self._inner.set_parameters(params)

    def get_state(self) -> dict[str, Any]:
        return self._inner.get_state()

    def reset(self) -> None:
        self._inner.reset()

    def _enrich(
        self, context: StrategyContext, instrument_id: str, mid: Decimal
    ) -> StrategyContext:
        bid = mid - self._half
        ask = mid + self._half
        if bid <= 0:
            bid = mid * Decimal("0.99") if mid > 0 else Decimal("1")
            ask = mid * Decimal("1.01") if mid > 0 else Decimal("2")
        inv = Decimal("0")
        if context.portfolio_state is not None:
            for p in context.portfolio_state.positions:
                if p.instrument_id == instrument_id:
                    inv = p.quantity
                    break
        max_pos = Decimal(str(self._inner.get_parameters().get("max_pos", "10")))
        skew = (inv / max_pos) if max_pos > 0 else Decimal("0")
        merged = {
            **dict(context.parameters),
            **self._inner.get_parameters(),
            "best_bid": str(bid),
            "best_ask": str(ask),
            "inventory": str(inv),
            "inventory_skew": str(skew),
        }
        return StrategyContext(
            clock=context.clock,
            portfolio_state=context.portfolio_state,
            parameters=merged,
        )


def maybe_wrap_for_bar_backtest(strategy_id: str, strategy: Strategy) -> Strategy:
    """Envuelve MM para lab backtest bar-based; resto sin cambio."""
    if is_mm_strategy(strategy_id):
        return BarSyntheticBookAdapter(strategy)
    return strategy
