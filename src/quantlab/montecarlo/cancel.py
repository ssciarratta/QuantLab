"""Cancelación cooperativa para corridas Monte Carlo."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass
class CancellationToken:
    """Señal cooperativa: el worker consulta ``is_cancelled`` entre batches."""

    _event: threading.Event = field(default_factory=threading.Event)

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            from quantlab.core.exceptions import ValidationError

            raise ValidationError("montecarlo cancelado por el usuario")
