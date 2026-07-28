"""Universo de monedas para UI Simulador (nombre completo + ticker)."""

from __future__ import annotations

from typing import Any

# Curado lab: display estable sin depender de red. underlying = ticker base.
SIM_COINS: tuple[dict[str, str], ...] = (
    {"id": "BTC", "name": "Bitcoin", "label": "Bitcoin (BTC)"},
    {"id": "ETH", "name": "Ethereum", "label": "Ethereum (ETH)"},
    {"id": "SOL", "name": "Solana", "label": "Solana (SOL)"},
    {"id": "BNB", "name": "BNB", "label": "BNB (BNB)"},
    {"id": "XRP", "name": "XRP", "label": "XRP (XRP)"},
    {"id": "ADA", "name": "Cardano", "label": "Cardano (ADA)"},
    {"id": "DOGE", "name": "Dogecoin", "label": "Dogecoin (DOGE)"},
    {"id": "AVAX", "name": "Avalanche", "label": "Avalanche (AVAX)"},
    {"id": "LINK", "name": "Chainlink", "label": "Chainlink (LINK)"},
    {"id": "DOT", "name": "Polkadot", "label": "Polkadot (DOT)"},
    {"id": "MATIC", "name": "Polygon", "label": "Polygon (MATIC)"},
    {"id": "NEAR", "name": "NEAR Protocol", "label": "NEAR Protocol (NEAR)"},
    {"id": "ATOM", "name": "Cosmos", "label": "Cosmos (ATOM)"},
    {"id": "LTC", "name": "Litecoin", "label": "Litecoin (LTC)"},
    {"id": "UNI", "name": "Uniswap", "label": "Uniswap (UNI)"},
    {"id": "APT", "name": "Aptos", "label": "Aptos (APT)"},
    {"id": "ARB", "name": "Arbitrum", "label": "Arbitrum (ARB)"},
    {"id": "OP", "name": "Optimism", "label": "Optimism (OP)"},
    {"id": "SUI", "name": "Sui", "label": "Sui (SUI)"},
    {"id": "PEPE", "name": "Pepe", "label": "Pepe (PEPE)"},
)

VENUE_LABELS: dict[str, str] = {
    "binance": "Binance",
    "okx": "OKX",
    "bybit": "Bybit",
    "hyperliquid": "Hyperliquid",
}


def list_sim_universe() -> dict[str, Any]:
    """Catálogo para selects UI (sin red)."""
    coins = [dict(c) for c in SIM_COINS]
    venues = [
        {"id": vid, "name": label, "label": f"{label} ({vid})"}
        for vid, label in VENUE_LABELS.items()
    ]
    return {
        "ok": True,
        "kind": "sim_universe",
        "coins": coins,
        "venues": venues,
        "note": (
            "underlying = id (ej. BTC). Cada venue resuelve su símbolo "
            "(BTCUSDT, BTC-USDT-SWAP, etc.)."
        ),
    }
