"""Journal JSONL de fills del PaperBroker (≠ LocalPaperLedger)."""

from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from quantlab.brokers.types import PaperFill
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.serialization import dataclass_to_dict

# Columnas estables para GET /api/paper/fills.csv (F65) — alineadas al export client F28.
FILLS_CSV_COLUMNS: tuple[str, ...] = (
    "ts",
    "fill_id",
    "order_id",
    "symbol",
    "side",
    "quantity",
    "price",
    "source",
)


def _csv_escape(value: object) -> str:
    s = "" if value is None else str(value)
    if any(ch in s for ch in (",", '"', "\n", "\r")):
        return '"' + s.replace('"', '""') + '"'
    return s


def fills_to_csv(fills: list[PaperFill]) -> str:
    """Serializa fills paper a CSV (header + rows, trailing newline)."""
    lines = [",".join(FILLS_CSV_COLUMNS)]
    for fill in fills:
        payload = dataclass_to_dict(fill)
        lines.append(
            ",".join(_csv_escape(payload.get(col, "")) for col in FILLS_CSV_COLUMNS)
        )
    return "\n".join(lines) + "\n"


class PaperFillJournal:
    """Append-only JSONL de ``PaperFill`` (source=paper_broker).

    No mezclar con ``LocalPaperLedger`` (SQLite de sims research).
    """

    SOURCE_TAG = "paper_broker"

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def append(self, fill: PaperFill) -> None:
        if fill.source != self.SOURCE_TAG:
            raise ValidationError(
                f"PaperFill.source debe ser {self.SOURCE_TAG!r}, got {fill.source!r}"
            )
        line = json.dumps(dataclass_to_dict(fill), sort_keys=True) + "\n"
        # atomic-ish: append + fsync (no reescribe el archivo completo)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())

    def list_fills(self) -> list[PaperFill]:
        if not self._path.exists():
            return []
        fills: list[PaperFill] = []
        text = self._path.read_text(encoding="utf-8")
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            payload = json.loads(line)
            fills.append(
                PaperFill(
                    fill_id=str(payload["fill_id"]),
                    order_id=str(payload["order_id"]),
                    symbol=str(payload["symbol"]),
                    side=str(payload["side"]),
                    quantity=Decimal(str(payload["quantity"])),
                    price=Decimal(str(payload["price"])),
                    ts=datetime.fromisoformat(str(payload["ts"])),
                    source=str(payload.get("source", self.SOURCE_TAG)),
                )
            )
        return fills

    def export_csv(self) -> str:
        """CSV text/csv del journal (header + rows)."""
        return fills_to_csv(self.list_fills())
