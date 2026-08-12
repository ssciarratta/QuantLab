"""Blindaje Windows: tqdm/HF imprimen █ y tumban el Scanner en consolas ASCII.

El error típico es::

    UnicodeEncodeError: 'ascii' codec can't encode characters in position 26-29

porque la barra de progreso cae a mitad de línea (``…|████|…``).
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
from collections.abc import Iterator
from typing import TextIO


def harden_progress_env() -> None:
    """Env vars antes de tocar HuggingFace / tqdm (forzado, no setdefault)."""
    os.environ["TQDM_ASCII"] = "1"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def reconfigure_stdio_utf8() -> None:
    """Reconfigura stdout/stderr a UTF-8 con replace (nunca UnicodeEncodeError)."""
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            with contextlib.suppress(Exception):
                reconf(encoding="utf-8", errors="replace")


class _ReplaceWriter(io.TextIOBase):
    """Proxy que escribe al stream original con errors=replace."""

    def __init__(self, target: TextIO) -> None:
        self._target = target
        enc = getattr(target, "encoding", None) or "utf-8"
        self._encoding = enc

    @property
    def encoding(self) -> str:  # type: ignore[override]
        return "utf-8"

    def write(self, s: str) -> int:
        if not s:
            return 0
        try:
            return int(self._target.write(s))
        except UnicodeEncodeError:
            safe = s.encode(self._encoding, errors="replace").decode(
                self._encoding, errors="replace"
            )
            return int(self._target.write(safe))

    def flush(self) -> None:
        with contextlib.suppress(Exception):
            self._target.flush()

    def isatty(self) -> bool:
        return bool(getattr(self._target, "isatty", lambda: False)())


@contextlib.contextmanager
def safe_stdio() -> Iterator[None]:
    """Durante carga/inferencia Kronos: env + stdio a prueba de █ / ñ / —."""
    harden_progress_env()
    reconfigure_stdio_utf8()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = _ReplaceWriter(old_out)
    sys.stderr = _ReplaceWriter(old_err)
    try:
        yield
    finally:
        sys.stdout = old_out
        sys.stderr = old_err


__all__ = [
    "harden_progress_env",
    "reconfigure_stdio_utf8",
    "safe_stdio",
]
