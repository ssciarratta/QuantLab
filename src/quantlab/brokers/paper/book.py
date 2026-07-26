"""PaperBook — posiciones, cash y equity MTM del plano paper."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.brokers.types import BrokerAccount, BrokerPosition, PaperFill
from quantlab.core.exceptions import ValidationError

DEFAULT_INITIAL_CASH = Decimal("100000")


class PaperBook:
    """Libro paper mutable controlado (fail-closed: no short por defecto).

    Estado interno mutable; serialización vía ``to_dict`` / ``from_dict``.
    """

    def __init__(
        self,
        initial_cash: Decimal = DEFAULT_INITIAL_CASH,
        *,
        currency: str = "USD",
        allow_short: bool = False,
        cash: Decimal | None = None,
        positions: dict[str, tuple[Decimal, Decimal]] | None = None,
    ) -> None:
        if not initial_cash.is_finite() or initial_cash < 0:
            raise ValidationError("initial_cash debe ser finito y no negativo")
        resolved_cash = Decimal(cash) if cash is not None else Decimal(initial_cash)
        if not resolved_cash.is_finite() or resolved_cash < 0:
            raise ValidationError("cash no puede ser negativo ni no-finito")
        if not currency.strip():
            raise ValidationError("currency no puede ser vacío")
        self._initial_cash = Decimal(initial_cash)
        self._cash = resolved_cash
        self._currency = currency
        self._allow_short = allow_short
        # symbol -> (quantity, avg_price)
        raw_positions = dict(positions or {})
        for sym, (qty, avg) in raw_positions.items():
            if (
                not sym.strip()
                or not qty.is_finite()
                or qty == 0
                or not avg.is_finite()
                or avg < 0
            ):
                raise ValidationError(f"posición inválida para {sym!r}")
            if not allow_short and qty < 0:
                raise ValidationError(
                    f"short no permitido: posición {sym} qty={qty} (allow_short=False)"
                )
        self._positions: dict[str, tuple[Decimal, Decimal]] = raw_positions

    @property
    def initial_cash(self) -> Decimal:
        return self._initial_cash

    @property
    def cash(self) -> Decimal:
        return self._cash

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def allow_short(self) -> bool:
        return self._allow_short

    def apply_fill(self, fill: PaperFill) -> None:
        """Aplica un fill: actualiza cash y posiciones (avg ponderado)."""
        if fill.quantity <= 0:
            raise ValidationError("fill.quantity debe ser > 0")
        if fill.price < 0:
            raise ValidationError("fill.price no puede ser negativo")

        side = fill.side.strip().lower()
        qty = Decimal(fill.quantity)
        price = Decimal(fill.price)
        notional = qty * price
        cur_qty, cur_avg = self._positions.get(fill.symbol, (Decimal("0"), Decimal("0")))

        if side == "buy":
            new_cash = self._cash - notional
            if new_cash < 0:
                raise ValidationError(
                    f"cash insuficiente para BUY {fill.symbol}: need {notional}, have {self._cash}"
                )
            new_qty = cur_qty + qty
            if new_qty == 0:
                self._positions.pop(fill.symbol, None)
            elif cur_qty >= 0:
                new_avg = (cur_qty * cur_avg + qty * price) / new_qty
                self._positions[fill.symbol] = (new_qty, new_avg)
            elif new_qty > 0:
                # cubrió short y quedó long
                self._positions[fill.symbol] = (new_qty, price)
            else:
                # sigue short (allow_short)
                self._positions[fill.symbol] = (new_qty, cur_avg)
            self._cash = new_cash
            return

        if side == "sell":
            new_qty = cur_qty - qty
            if new_qty < 0 and not self._allow_short:
                raise ValidationError(
                    f"short no permitido: SELL {fill.symbol} dejaría qty={new_qty}"
                )
            new_cash = self._cash + notional
            if new_qty == 0:
                self._positions.pop(fill.symbol, None)
            elif new_qty < 0:
                self._positions[fill.symbol] = (new_qty, price)
            else:
                self._positions[fill.symbol] = (new_qty, cur_avg)
            self._cash = new_cash
            return

        raise ValidationError(f"fill.side inválido: {fill.side!r}")

    def get_positions(self) -> list[BrokerPosition]:
        return [
            BrokerPosition(symbol=sym, quantity=qty, avg_price=avg)
            for sym, (qty, avg) in sorted(self._positions.items())
            if qty != 0
        ]

    def get_account(self, mark_prices: dict[str, Decimal] | None = None) -> BrokerAccount:
        """Equity = cash + mark-to-market de posiciones (fallback avg_price)."""
        marks = mark_prices or {}
        mtm = Decimal("0")
        for sym, (qty, avg) in self._positions.items():
            mark = marks.get(sym, avg)
            mtm += qty * mark
        equity = self._cash + mtm
        return BrokerAccount(cash=self._cash, currency=self._currency, equity=equity)

    def get_pnl(self, mark_prices: dict[str, Decimal] | None = None) -> dict[str, Decimal]:
        """PnL summary: realized / unrealized / equity / cash (F67).

        Convención (sin fees en PnL bruto, alineado TD-17):
        - ``cost`` = Σ(qty × avg_price) de posiciones abiertas
        - ``mtm`` = Σ(qty × mark) (fallback avg)
        - ``unrealized`` = mtm − cost
        - ``realized`` = cash + cost − initial_cash
        - ``equity`` = cash + mtm = initial_cash + realized + unrealized
        """
        marks = mark_prices or {}
        cost = Decimal("0")
        mtm = Decimal("0")
        for sym, (qty, avg) in self._positions.items():
            mark = marks.get(sym, avg)
            cost += qty * avg
            mtm += qty * mark
        unrealized = mtm - cost
        realized = self._cash + cost - self._initial_cash
        equity = self._cash + mtm
        return {
            "cash": self._cash,
            "equity": equity,
            "realized": realized,
            "unrealized": unrealized,
            "initial_cash": self._initial_cash,
        }

    def to_dict(self) -> dict[str, Any]:
        positions: dict[str, dict[str, str]] = {}
        for sym, (qty, avg) in sorted(self._positions.items()):
            positions[sym] = {"quantity": str(qty), "avg_price": str(avg)}
        return {
            "initial_cash": str(self._initial_cash),
            "cash": str(self._cash),
            "currency": self._currency,
            "allow_short": self._allow_short,
            "positions": positions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PaperBook:
        if not isinstance(data, dict):
            raise ValidationError("PaperBook.from_dict espera dict")
        try:
            initial_cash = Decimal(str(data.get("initial_cash", DEFAULT_INITIAL_CASH)))
            cash = Decimal(str(data.get("cash", initial_cash)))
        except Exception as exc:
            raise ValidationError(f"cash inválido en book: {exc}") from exc
        currency = str(data.get("currency", "USD"))
        allow_short_raw = data.get("allow_short", False)
        if not isinstance(allow_short_raw, bool):
            raise ValidationError("allow_short debe ser bool")
        allow_short = allow_short_raw
        raw_pos = data.get("positions") or {}
        if not isinstance(raw_pos, dict):
            raise ValidationError("positions debe ser objeto")
        positions: dict[str, tuple[Decimal, Decimal]] = {}
        for sym, payload in raw_pos.items():
            if not isinstance(payload, dict):
                raise ValidationError(f"posición inválida para {sym}")
            try:
                positions[str(sym)] = (
                    Decimal(str(payload["quantity"])),
                    Decimal(str(payload["avg_price"])),
                )
            except Exception as exc:
                raise ValidationError(f"posición inválida para {sym}: {exc}") from exc
        return cls(
            initial_cash=initial_cash,
            currency=currency,
            allow_short=allow_short,
            cash=cash,
            positions=positions,
        )
