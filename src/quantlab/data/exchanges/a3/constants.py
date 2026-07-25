"""Constantes y enums propios de QuantLab para A3 (sin pyRofex)."""

from __future__ import annotations

from enum import StrEnum

PROVIDER_ID = "a3"
SCHEMA_VERSION_RAW = "1.0"
SCHEMA_VERSION_BARS = "1.0"

BAR_TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m", "30m", "1h", "1d")

LIVE_TRADING_CONFIRMATION = "I_UNDERSTAND_THIS_SENDS_REAL_ORDERS"


class A3EnvironmentName(StrEnum):
    SIMULATION = "simulation"
    PRODUCTION = "production"


class KillSwitchScope(StrEnum):
    ALL_ORDERS = "all_orders"
    PRODUCTION_ONLY = "production_only"
    ACCOUNT = "account"
    SYMBOL = "symbol"
