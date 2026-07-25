"""Validación A3 — reexport quality + config checks."""

from quantlab.data.exchanges.a3.config import load_a3_config
from quantlab.data.quality.validators import validate_bars, validate_trades

__all__ = ["load_a3_config", "validate_bars", "validate_trades"]
