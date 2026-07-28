"""Mapeo subyacente → símbolo por venue y tipo de mercado."""

from __future__ import annotations

from dataclasses import dataclass

from quantlab.core.exceptions import ValidationError

VENUES = frozenset({"binance", "okx", "bybit", "hyperliquid", "a3"})
MARKET_TYPES = frozenset({"spot", "futures"})


@dataclass(frozen=True, slots=True)
class ResolvedInstrument:
    venue: str
    market_type: str
    underlying: str
    symbol: str
    instrument_id: str


def _normalize_crypto_underlying(raw: str) -> str:
    text = raw.strip().upper().replace("/", "").replace("-", "")
    if text.endswith("USDT"):
        text = text[: -len("USDT")]
    if text.endswith("SWAP"):
        text = text[: -len("SWAP")]
    if not text or not text.isalnum():
        raise ValidationError(f"underlying inválido: {raw!r}")
    return text


def _normalize_hl_underlying(raw: str) -> str:
    """HL core = BTC; HIP-3 = ``xyz:GOLD`` (case-sensitive)."""
    text = raw.strip()
    if not text:
        raise ValidationError(f"underlying inválido: {raw!r}")
    if ":" in text:
        # No upper: candleSnapshot exige el case exacto del meta.
        return text
    return _normalize_crypto_underlying(text)


def resolve_instrument(
    underlying: str,
    *,
    venue: str,
    market_type: str = "futures",
) -> ResolvedInstrument:
    """Resuelve BTC+okx+futures → BTC-USDT-SWAP; A3 → ticker con vencimiento."""
    v = venue.strip().lower()
    mt = market_type.strip().lower()
    if v not in VENUES:
        raise ValidationError(f"venue desconocido: {venue!r}")
    if mt not in MARKET_TYPES:
        raise ValidationError(f"market_type inválido: {market_type!r}")

    if v == "a3":
        if mt != "futures":
            raise ValidationError("a3 solo soporta futures (contratos con vencimiento)")
        sym = underlying.strip().upper()
        if not sym or len(sym) < 3:
            raise ValidationError(f"símbolo A3 inválido: {underlying!r}")
        return ResolvedInstrument(
            venue="a3",
            market_type="futures",
            underlying=sym,
            symbol=sym,
            instrument_id=f"A3:{sym}",
        )

    if v == "hyperliquid":
        base = _normalize_hl_underlying(underlying)
        return ResolvedInstrument(
            venue="hyperliquid",
            market_type=mt,
            underlying=base,
            symbol=base,
            instrument_id=f"HL:{base}",
        )

    base = _normalize_crypto_underlying(underlying)
    if v == "binance":
        sym = f"{base}USDT"
        prefix = "BNF" if mt == "futures" else "BN"
    elif v == "okx":
        sym = f"{base}-USDT-SWAP" if mt == "futures" else f"{base}-USDT"
        prefix = "OKX"
    elif v == "bybit":
        sym = f"{base}USDT"
        prefix = "BYB"
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
