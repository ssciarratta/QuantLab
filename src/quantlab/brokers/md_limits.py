"""Límites de klines del lab (MD público multi-venue)."""

from __future__ import annotations

# Mínimo usable para estrategias / overlay
MIN_KLINES = 3

# Validación en router / lab services / sim compare
LAB_KLINE_LIMIT_MIN = 8

# Tope de producto (no de la API por request). Adapters paginan hasta aquí.
# 525_600 = 365 d × 24 h × 60 min → 1 año @ 1m (cubre “cualquier” período del UI).
# Runs grandes (decenas de miles de velas × varios venues) son lentos y pesan en RAM.
LAB_KLINE_LIMIT_MAX = 525_600

# Alias histórico usado por adapters Binance / OKX / Bybit / HL
MAX_KLINES_TOTAL = LAB_KLINE_LIMIT_MAX

# Umbral UI: avisar que el run será pesado (sin bloquear).
# 40_000 → 1 mes @ 1m (43_200) ya avisa en naranja.
LAB_KLINE_HEAVY_WARN = 40_000
