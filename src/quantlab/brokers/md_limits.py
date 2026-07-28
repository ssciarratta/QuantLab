"""Límites de klines del lab (MD público multi-venue)."""

from __future__ import annotations

# Mínimo usable para estrategias / overlay
MIN_KLINES = 3

# Validación en router / lab services / sim compare
LAB_KLINE_LIMIT_MIN = 8

# 1 año @ 1h ≈ 8760. Cap de producto (no de la API).
# Adapters deben paginar hasta este tope; no truncar en silencio.
LAB_KLINE_LIMIT_MAX = 8760

# Alias histórico usado por adapters Binance
MAX_KLINES_TOTAL = LAB_KLINE_LIMIT_MAX
