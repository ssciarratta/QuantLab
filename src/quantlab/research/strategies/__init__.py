"""Implementaciones de Strategy."""

from quantlab.research.strategies.avellaneda_stoikov import (
    AvellanedaStoikovStrategy,
    optimal_half_spread,
    quote_prices,
    reservation_price,
)
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.research.strategies.classic_bar import ClassicBarStrategy
from quantlab.research.strategies.dummy_strategy import DummyStrategy
from quantlab.research.strategies.inventory_mm import InventoryMMStrategy
from quantlab.research.strategies.mm_spectrum import (
    AdaptiveMMStrategy,
    DynamicSpreadMMStrategy,
    MultiLevelMMStrategy,
)
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy

__all__ = [
    "AdaptiveMMStrategy",
    "AvellanedaStoikovStrategy",
    "BuyOnceStrategy",
    "ClassicBarStrategy",
    "DummyStrategy",
    "DynamicSpreadMMStrategy",
    "InventoryMMStrategy",
    "MultiLevelMMStrategy",
    "SimpleMomentumStrategy",
    "optimal_half_spread",
    "quote_prices",
    "reservation_price",
]
