"""Mapeo DTO A3 → dominio QuantLab (sin importar pyRofex)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.core.types.enums import InstrumentStatus, OrderSide
from quantlab.core.types.instrument import Instrument
from quantlab.core.types.market import BookLevel, Trade
from quantlab.data.exchanges.a3.exceptions import A3MappingError
from quantlab.data.exchanges.a3.models import (
    A3BookLevelDTO,
    A3InstrumentDTO,
    A3MarketSnapshotDTO,
    A3TradeDTO,
)

_SAFE_SYMBOL_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_symbol_for_path(symbol: str) -> str:
    cleaned = _SAFE_SYMBOL_RE.sub("_", symbol.strip())
    return cleaned or "UNKNOWN"


class A3SymbolMapper:
    """Mapper determinista de símbolos A3."""

    def normalize(self, symbol: str) -> str:
        return symbol.strip().upper()

    def to_path_safe(self, symbol: str) -> str:
        return sanitize_symbol_for_path(self.normalize(symbol))


def _dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise A3MappingError(f"valor decimal inválido: {value!r}") from exc


def _aware(ts: Any) -> datetime:
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=UTC)
        return ts
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(float(ts), tz=UTC)
    if isinstance(ts, str):
        text = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt
    raise A3MappingError(f"timestamp no soportado: {ts!r}")


def parse_instrument_dto(raw: dict[str, Any]) -> A3InstrumentDTO:
    symbol = str(raw.get("symbol") or raw.get("instrumentId", {}).get("symbol") or "")
    if not symbol.strip():
        raise A3MappingError("instrumento sin símbolo")
    return A3InstrumentDTO(
        symbol=symbol.strip(),
        description=(str(raw["description"]) if raw.get("description") is not None else None),
        market=(str(raw["marketId"]) if raw.get("marketId") is not None else None),
        segment=(str(raw["segment"]) if raw.get("segment") is not None else None),
        currency=(str(raw["currency"]) if raw.get("currency") is not None else None),
        cfi_code=(str(raw["cficode"]) if raw.get("cficode") is not None else None),
        tick_size=_dec(raw.get("tickIncrement") or raw.get("minPriceIncrement")),
        contract_multiplier=_dec(raw.get("contractMultiplier") or raw.get("priceFactor")),
        lot_size=_dec(raw.get("minLotSize") or raw.get("lotSize") or raw.get("roundLot")),
        maturity=(str(raw["maturityDate"]) if raw.get("maturityDate") is not None else None),
        underlying=(str(raw["underlying"]) if raw.get("underlying") is not None else None),
        status=(str(raw["securityStatus"]) if raw.get("securityStatus") is not None else None),
        raw=dict(raw),
    )


def instrument_dto_to_domain(dto: A3InstrumentDTO) -> Instrument:
    tick = dto.tick_size or Decimal("0.01")
    lot = dto.lot_size or Decimal("1")
    # min_notional: si no hay dato, documentamos vía metadata (no inventamos negocio)
    min_notional = tick * lot
    base = dto.underlying or dto.symbol.split("/")[0]
    quote = dto.currency or "ARS"
    if base.strip() == quote.strip():
        quote = "ARS" if quote != "ARS" else "USD"
    status = InstrumentStatus.ACTIVE
    if dto.status and dto.status.upper() in {"SUSPENDED", "DELISTED", "INACTIVE"}:
        status = InstrumentStatus.DELISTED
    return Instrument(
        instrument_id=f"a3:{dto.symbol}",
        symbol=dto.symbol,
        base_asset=base,
        quote_asset=quote,
        venue_id="a3",
        tick_size=tick,
        lot_size=lot,
        min_notional=min_notional,
        status=status,
        metadata={
            "provider": "a3",
            "description": dto.description,
            "market": dto.market,
            "segment": dto.segment,
            "cfi_code": dto.cfi_code,
            "maturity": dto.maturity,
            "contract_multiplier": str(dto.contract_multiplier)
            if dto.contract_multiplier is not None
            else None,
            "external_status": dto.status,
            "fields_inferred": {
                "tick_size": dto.tick_size is None,
                "lot_size": dto.lot_size is None,
                "min_notional": True,
            },
        },
    )


def parse_trade_dto(symbol: str, raw: dict[str, Any]) -> A3TradeDTO:
    price = _dec(raw.get("price") or raw.get("Px"))
    size = _dec(raw.get("size") or raw.get("LastQty") or raw.get("quantity"))
    if price is None or size is None:
        raise A3MappingError("trade sin price/size")
    ts_raw = raw.get("datetime") or raw.get("timestamp") or raw.get("transactTime")
    if ts_raw is None:
        raise A3MappingError("trade sin timestamp")
    trade_id = raw.get("tradeId") or raw.get("execId") or raw.get("id")
    return A3TradeDTO(
        symbol=symbol,
        price=price,
        size=size,
        timestamp=_aware(ts_raw),
        trade_id=str(trade_id) if trade_id is not None else None,
        aggressor=(str(raw["aggressorSide"]) if raw.get("aggressorSide") is not None else None),
        raw=dict(raw),
    )


def trade_dto_to_domain(dto: A3TradeDTO) -> Trade:
    side = OrderSide.BUY
    if dto.aggressor and dto.aggressor.lower() in {"sell", "s", "offer", "ask"}:
        side = OrderSide.SELL
    return Trade(
        instrument_id=f"a3:{dto.symbol}",
        price=dto.price,
        quantity=dto.size,
        side=side,
        timestamp=dto.timestamp,
        trade_id=dto.trade_id or f"{dto.symbol}:{dto.timestamp.isoformat()}:{dto.price}:{dto.size}",
    )


def parse_snapshot_dto(symbol: str, raw: dict[str, Any]) -> A3MarketSnapshotDTO:
    market_obj = raw.get("marketData")
    market: dict[str, Any] = market_obj if isinstance(market_obj, dict) else raw
    bids_raw = market.get("BI") or market.get("bids") or []
    offers_raw = market.get("OF") or market.get("offers") or []
    bids: list[A3BookLevelDTO] = []
    offers: list[A3BookLevelDTO] = []
    for item in bids_raw:
        if isinstance(item, dict):
            p = _dec(item.get("price") or item.get("Px"))
            s = _dec(item.get("size") or item.get("BidSize") or item.get("quantity"))
            if p is not None and s is not None:
                bids.append(A3BookLevelDTO(price=p, size=s))
    for item in offers_raw:
        if isinstance(item, dict):
            p = _dec(item.get("price") or item.get("Px"))
            s = _dec(item.get("size") or item.get("OfferSize") or item.get("quantity"))
            if p is not None and s is not None:
                offers.append(A3BookLevelDTO(price=p, size=s))
    last_obj = market.get("LA") or market.get("last") or {}
    last: dict[str, Any] = last_obj if isinstance(last_obj, dict) else {}
    last_price = _dec(last.get("price"))
    last_size = _dec(last.get("size"))
    oi_obj = market.get("OI")
    oi = None
    if isinstance(oi_obj, dict):
        oi = _dec(oi_obj.get("size"))
    ts = market.get("timestamp") or raw.get("timestamp") or datetime.now(tz=UTC)
    return A3MarketSnapshotDTO(
        symbol=symbol,
        timestamp=_aware(ts),
        bids=tuple(bids),
        offers=tuple(offers),
        last_price=last_price,
        last_size=last_size,
        open_interest=oi,
        raw=dict(raw),
    )


def book_levels_to_domain(levels: tuple[A3BookLevelDTO, ...]) -> tuple[BookLevel, ...]:
    return tuple(BookLevel(price=x.price, quantity=x.size) for x in levels)
