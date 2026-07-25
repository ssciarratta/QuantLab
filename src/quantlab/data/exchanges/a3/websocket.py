"""Cliente WebSocket con cola acotada (sin trabajo pesado en callback)."""

from __future__ import annotations

import queue
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from quantlab.data.exchanges.a3.models import A3WsEnvelope


@dataclass
class WsCaptureStats:
    received: int = 0
    enqueued: int = 0
    dropped: int = 0
    errors: int = 0


@dataclass
class A3WebSocketCapture:
    """Captura MD/OR en cola; el procesamiento ocurre fuera del callback."""

    maxsize: int = 10000
    stats: WsCaptureStats = field(default_factory=WsCaptureStats)
    _queue: queue.Queue[A3WsEnvelope] = field(init=False)

    def __post_init__(self) -> None:
        self._queue = queue.Queue(maxsize=self.maxsize)

    def make_handler(self, message_type: str) -> Callable[[dict[str, Any]], None]:
        def _handler(message: dict[str, Any]) -> None:
            self.stats.received += 1
            envelope = A3WsEnvelope(
                message_type=message_type,
                received_at=datetime.now(tz=UTC),
                payload=dict(message),
            )
            try:
                self._queue.put_nowait(envelope)
                self.stats.enqueued += 1
            except queue.Full:
                self.stats.dropped += 1

        return _handler

    def drain(self, max_items: int = 1000) -> list[A3WsEnvelope]:
        items: list[A3WsEnvelope] = []
        for _ in range(max_items):
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return items
