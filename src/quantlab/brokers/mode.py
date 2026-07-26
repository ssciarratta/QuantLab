"""Modos operativos QuantLab (Fase 19).

REAL (producto) = PAPER: MD/cuenta reales + fills simulados. REAL ≠ LIVE.
"""

from __future__ import annotations

from enum import StrEnum

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED


class OperatingMode(StrEnum):
    """Modo de arranque del workbench / broker plane."""

    TESTER = "tester"
    PAPER = "paper"
    LIVE = "live"


# Alias de producto: el operador dice "REAL"; internamente es PAPER (sin órdenes venue).
REAL_ALIAS: OperatingMode = OperatingMode.PAPER


class ModeGuard:
    """Fail-closed al boot: LIVE no arranca mientras LIVE_BLOCKED."""

    @staticmethod
    def validate_boot(mode: OperatingMode) -> None:
        if mode is OperatingMode.LIVE and LIVE_BLOCKED:
            raise ValidationError(
                "OperatingMode.LIVE bloqueado: LIVE_BLOCKED=True. "
                "Usar TESTER o PAPER (alias REAL). Ver docs/ops/LIVE_FLIP_CHECKLIST.md"
            )


def resolve_mode(name: str) -> OperatingMode:
    """Resuelve nombre de modo (case-insensitive). 'real' → PAPER."""
    key = name.strip().lower()
    if key == "real":
        return REAL_ALIAS
    if key == "tester":
        return OperatingMode.TESTER
    if key == "paper":
        return OperatingMode.PAPER
    if key == "live":
        return OperatingMode.LIVE
    raise ValidationError(f"modo desconocido: {name!r} (tester|paper|real|live)")


def default_mode() -> OperatingMode:
    """Default seguro: TESTER (offline / fake backends)."""
    return OperatingMode.TESTER
