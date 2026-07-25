"""Provider genérico CSV (Fase 15 — segundo exchange stub)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import OrderSide
from quantlab.core.types.market import Trade


@dataclass(frozen=True, slots=True)
class GenericCsvProvider:
    """Lee trades OHLCV-minimos desde CSV: ts,price,qty,side,trade_id."""

    provider_id: str = "generic_csv"

    def load_trades(self, path: Path, *, instrument_id: str) -> tuple[Trade, ...]:
        if not path.exists():
            raise ValidationError(f"CSV no existe: {path}")
        out: list[Trade] = []
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                out.append(
                    Trade(
                        instrument_id=instrument_id,
                        price=Decimal(row["price"]),
                        quantity=Decimal(row["qty"]),
                        side=OrderSide(row["side"]),
                        timestamp=datetime.fromisoformat(row["ts"]),
                        trade_id=row["trade_id"],
                    )
                )
        return tuple(out)
