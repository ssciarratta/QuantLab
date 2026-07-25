"""Helpers causales (anti-lookahead) para transformers."""

from __future__ import annotations

from collections.abc import Sequence

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar


def assert_bars_causal_ready(bars: Sequence[Bar], *, min_lookback: int) -> None:
    if min_lookback < 1:
        raise ValidationError("min_lookback inválido")
    if len(bars) < min_lookback:
        raise ValidationError(f"se requieren al menos {min_lookback} barras; recibidas {len(bars)}")
    instrument = bars[0].instrument_id
    for i, bar in enumerate(bars):
        if bar.instrument_id != instrument:
            raise ValidationError("todas las barras deben compartir instrument_id")
        if i > 0 and bar.timestamp_close <= bars[i - 1].timestamp_close:
            raise ValidationError(
                "barras deben estar estrictamente ordenadas por timestamp_close asc"
            )


def causal_window(bars: Sequence[Bar], index: int, lookback: int) -> Sequence[Bar]:
    """Ventana inclusive ending at index: bars[index-lookback+1 : index+1]."""
    if index < 0 or index >= len(bars):
        raise ValidationError("índice fuera de rango")
    if lookback < 1:
        raise ValidationError("lookback inválido")
    start = index - lookback + 1
    if start < 0:
        raise ValidationError("ventana causal incompleta (lookahead implícito prohibido)")
    return bars[start : index + 1]
