"""Journal JSONL de fills del PaperBroker (≠ LocalPaperLedger)."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from typing import Any

from quantlab.brokers.paper.reconciliation import JournalCheckpoint
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
    MIRROR_SOURCE_TAGS = frozenset({SOURCE_TAG, "binance_demo"})

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    @property
    def path(self) -> Path:
        return self._path

    def append(self, fill: PaperFill) -> None:
        self._validate_fill(fill, line_number=None)
        with self._lock:
            fills = self._read_strict_unlocked()
            if any(existing.fill_id == fill.fill_id for existing in fills):
                raise ValidationError(f"duplicate fill_id rechazado: {fill.fill_id!r}")
            if any(existing.order_id == fill.order_id for existing in fills):
                raise ValidationError(f"duplicate order_id rechazado: {fill.order_id!r}")
            line = json.dumps(dataclass_to_dict(fill), sort_keys=True) + "\n"
            # Journal es el commit durable: append + flush + fsync.
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())

    def list_fills(self) -> list[PaperFill]:
        """Compatibilidad: desde F88 la lectura también es estricta."""
        return self.read_strict()

    def read_strict(self) -> list[PaperFill]:
        """Lee JSONL completo y rechaza cualquier registro ambiguo o corrupto."""
        with self._lock:
            return self._read_strict_unlocked()

    def checkpoint(self) -> JournalCheckpoint:
        """Checkpoint SHA-256 del archivo completo, luego de validarlo."""
        with self._lock:
            fills = self._read_strict_unlocked()
            raw = self._path.read_bytes() if self._path.exists() else b""
            return JournalCheckpoint(
                record_count=len(fills),
                last_fill_id=fills[-1].fill_id if fills else None,
                sha256=sha256(raw).hexdigest(),
            )

    def contains_checkpoint(self, checkpoint: JournalCheckpoint) -> bool:
        """True si ``checkpoint`` identifica exactamente un prefijo actual."""
        with self._lock:
            fills = self._read_strict_unlocked()
            if checkpoint.record_count > len(fills):
                return False
            raw = self._path.read_bytes() if self._path.exists() else b""
            lines = raw.splitlines(keepends=True)
            prefix = b"".join(lines[: checkpoint.record_count])
            last_fill_id = (
                fills[checkpoint.record_count - 1].fill_id
                if checkpoint.record_count
                else None
            )
            return (
                last_fill_id == checkpoint.last_fill_id
                and sha256(prefix).hexdigest() == checkpoint.sha256
            )

    def _read_strict_unlocked(self) -> list[PaperFill]:
        if not self._path.exists():
            return []
        try:
            raw = self._path.read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ValidationError(f"journal ilegible: {exc}") from exc
        if raw and not raw.endswith(b"\n"):
            line_number = raw.count(b"\n") + 1
            raise ValidationError(
                f"journal línea {line_number}: registro truncado (falta newline final)"
            )

        fills: list[PaperFill] = []
        fill_ids: set[str] = set()
        order_ids: set[str] = set()
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            if not raw_line.strip():
                raise ValidationError(f"journal línea {line_number}: línea vacía")
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    f"journal línea {line_number}: JSON inválido: {exc.msg}"
                ) from exc
            if not isinstance(payload, dict):
                raise ValidationError(
                    f"journal línea {line_number}: registro debe ser objeto JSON"
                )
            fill = self._fill_from_payload(payload, line_number)
            if fill.fill_id in fill_ids:
                raise ValidationError(
                    f"journal línea {line_number}: duplicate fill_id {fill.fill_id!r}"
                )
            if fill.order_id in order_ids:
                raise ValidationError(
                    f"journal línea {line_number}: duplicate order_id {fill.order_id!r}"
                )
            fill_ids.add(fill.fill_id)
            order_ids.add(fill.order_id)
            fills.append(fill)
        return fills

    def _fill_from_payload(self, payload: dict[str, Any], line_number: int) -> PaperFill:
        required = ("fill_id", "order_id", "symbol", "side", "quantity", "price", "ts", "source")
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValidationError(
                f"journal línea {line_number}: campos requeridos ausentes: {', '.join(missing)}"
            )
        for key in ("fill_id", "order_id", "symbol", "side", "ts", "source"):
            if not isinstance(payload[key], str):
                raise ValidationError(
                    f"journal línea {line_number}: {key} debe ser string"
                )
        try:
            quantity = Decimal(str(payload["quantity"]))
            price = Decimal(str(payload["price"]))
            ts = datetime.fromisoformat(str(payload["ts"]))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValidationError(f"journal línea {line_number}: fill inválido: {exc}") from exc
        fill = PaperFill(
            fill_id=str(payload["fill_id"]),
            order_id=str(payload["order_id"]),
            symbol=str(payload["symbol"]),
            side=str(payload["side"]),
            quantity=quantity,
            price=price,
            ts=ts,
            source=str(payload["source"]),
        )
        self._validate_fill(fill, line_number=line_number)
        return fill

    @classmethod
    def _validate_fill(cls, fill: PaperFill, *, line_number: int | None) -> None:
        prefix = f"journal línea {line_number}: " if line_number is not None else ""
        if fill.source not in cls.MIRROR_SOURCE_TAGS:
            raise ValidationError(
                f"{prefix}PaperFill.source debe ser uno de "
                f"{sorted(cls.MIRROR_SOURCE_TAGS)!r}, got {fill.source!r}"
            )
        if not fill.fill_id.strip() or not fill.order_id.strip() or not fill.symbol.strip():
            raise ValidationError(f"{prefix}fill_id, order_id y symbol deben ser no vacíos")
        if fill.side.strip().lower() not in {"buy", "sell"}:
            raise ValidationError(f"{prefix}fill.side inválido: {fill.side!r}")
        if not fill.quantity.is_finite() or fill.quantity <= 0:
            raise ValidationError(f"{prefix}fill.quantity debe ser finito y > 0")
        if not fill.price.is_finite() or fill.price < 0:
            raise ValidationError(f"{prefix}fill.price debe ser finito y >= 0")
        if fill.ts.tzinfo is None or fill.ts.utcoffset() is None:
            raise ValidationError(f"{prefix}fill.ts debe incluir timezone")

    def export_csv(self) -> str:
        """CSV text/csv del journal (header + rows)."""
        return fills_to_csv(self.list_fills())
