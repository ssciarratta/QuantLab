"""Mapeo subyacente → símbolo por venue y tipo de mercado."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.core.exceptions import ValidationError

VENUES = frozenset({"binance", "okx", "bybit", "hyperliquid"})
MARKET_TYPES = frozenset({"spot", "futures"})


@dataclass(frozen=True, slots=True)
class ResolvedInstrument:
    venue: str
    market_type: str
    underlying: str
    symbol: str
    instrument_id: str


def _normalize_underlying(raw: str) -> str:
    text = raw.strip().upper().replace("/", "").replace("-", "")
    if text.endswith("USDT"):
        text = text[: -len("USDT")]
    if not text or not text.isalnum():
        raise ValidationError(f"underlying inválido: {raw!r}")
    return text


def resolve_instrument(
    underlying: str,
    *,
    venue: str,
    market_type: str = "futures",
) -> ResolvedInstrument:
    """Resuelve BTC + okx + futures → BTC-USDT-SWAP / OKX:BTC-USDT-SWAP."""
    base = _normalize_underlying(underlying)
    v = venue.strip().lower()
    mt = market_type.strip().lower()
    if v not in VENUES:
        raise ValidationError(f"venue desconocido: {venue!r}")
    if mt not in MARKET_TYPES:
        raise ValidationError(f"market_type inválido: {market_type!r}")

    if v == "binance":
        sym = f"{base}USDT"
        prefix = "BNF" if mt == "futures" else "BN"
    elif v == "okx":
        sym = f"{base}-USDT-SWAP" if mt == "futures" else f"{base}-USDT"
        prefix = "OKX"
    elif v == "bybit":
        sym = f"{base}USDT"
        prefix = "BYB"
    elif v == "hyperliquid":
        sym = base
        prefix = "HL"
    else:
        raise ValidationError(f"venue no soportado: {venue!r}")

    iid = f"{prefix}:{sym}"
    return ResolvedInstrument(
        venue=v,
        market_type=mt,
        underlying=base,
        symbol=sym,
        instrument_id=iid,
    )
