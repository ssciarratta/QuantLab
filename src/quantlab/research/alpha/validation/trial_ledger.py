"""Registro de trials para Deflated Sharpe honesto."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class TrialRecord:
    trial_id: str
    detector_id: str
    signal_type: str
    symbols: tuple[str, ...]
    lag: int | None
    lookback: int
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())


class TrialLedger:
    """Conteo acumulado de pruebas (persistencia JSONL opcional)."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._records: list[TrialRecord] = []
        if path is not None and path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    raw = json.loads(line)
                    self._records.append(
                        TrialRecord(
                            trial_id=raw["trial_id"],
                            detector_id=raw["detector_id"],
                            signal_type=raw["signal_type"],
                            symbols=tuple(raw["symbols"]),
                            lag=raw.get("lag"),
                            lookback=int(raw.get("lookback") or 0),
                            metadata=dict(raw.get("metadata") or {}),
                            created_at=str(raw.get("created_at", "")),
                        )
                    )

    @property
    def path(self) -> Path | None:
        return self._path

    def log(
        self,
        *,
        trial_id: str,
        detector_id: str,
        signal_type: str,
        symbols: tuple[str, ...],
        lag: int | None = None,
        lookback: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> TrialRecord:
        rec = TrialRecord(
            trial_id=trial_id,
            detector_id=detector_id,
            signal_type=signal_type,
            symbols=symbols,
            lag=lag,
            lookback=lookback,
            metadata=dict(metadata or {}),
        )
        self._records.append(rec)
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(
                    json.dumps(
                        {
                            "trial_id": rec.trial_id,
                            "detector_id": rec.detector_id,
                            "signal_type": rec.signal_type,
                            "symbols": list(rec.symbols),
                            "lag": rec.lag,
                            "lookback": rec.lookback,
                            "metadata": rec.metadata,
                            "created_at": rec.created_at,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
        return rec

    def count(self) -> int:
        return len(self._records)

    def records(self) -> tuple[TrialRecord, ...]:
        return tuple(self._records)
