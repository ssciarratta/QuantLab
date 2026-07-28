"""Cálculo período → cantidad de velas (UI + API)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.brokers.md_limits import LAB_KLINE_LIMIT_MAX
from quantlab.core.exceptions import ValidationError

# Temporalidades estilo Binance Spot/Futures USDT (lab)
BINANCE_INTERVALS: tuple[str, ...] = (
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
)

_INTERVAL_MINUTES: dict[str, Decimal] = {
    "1m": Decimal("1"),
    "3m": Decimal("3"),
    "5m": Decimal("5"),
    "15m": Decimal("15"),
    "30m": Decimal("30"),
    "1h": Decimal("60"),
    "2h": Decimal("120"),
    "4h": Decimal("240"),
    "6h": Decimal("360"),
    "8h": Decimal("480"),
    "12h": Decimal("720"),
    "1d": Decimal("1440"),
    "3d": Decimal("4320"),
    "1w": Decimal("10080"),
    "1M": Decimal("43200"),  # aprox 30d
}

PERIOD_PRESETS_DAYS: dict[str, Decimal] = {
    "1d": Decimal("1"),
    "1w": Decimal("7"),
    "1M": Decimal("30"),
    "3M": Decimal("90"),
    "6M": Decimal("180"),
    "1Y": Decimal("365"),
}


def interval_minutes(interval: str) -> Decimal:
    key = interval.strip()
    if key not in _INTERVAL_MINUTES:
        raise ValidationError(
            f"interval inválido: {interval!r}; "
            f"permitidos: {', '.join(BINANCE_INTERVALS)}"
        )
    return _INTERVAL_MINUTES[key]


def estimate_n_bars(
    *,
    period_days: Decimal | float | int | str,
    interval: str,
) -> dict[str, Any]:
    """Devuelve cuántas velas comprende período × intervalo."""
    try:
        days = Decimal(str(period_days))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"period_days inválido: {period_days!r}") from exc
    if days <= 0:
        raise ValidationError("period_days debe ser > 0")
    mins = interval_minutes(interval)
    total_mins = days * Decimal("1440")
    n = int(total_mins // mins)
    if n < 1:
        n = 1
    return {
        "ok": True,
        "period_days": str(days),
        "interval": interval.strip(),
        "interval_minutes": str(mins),
        "n_bars": n,
        "n_bars_display": f"≈ {n:,} velas".replace(",", "."),
        "exceeds_lab_cap": n > LAB_KLINE_LIMIT_MAX,
        "exceeds_lab_cap_3000": n > LAB_KLINE_LIMIT_MAX,  # alias legacy UI
        "lab_kline_limit_max": LAB_KLINE_LIMIT_MAX,
        "note": (
            f"Si n_bars > {LAB_KLINE_LIMIT_MAX} el lab trunca o pide intervalo más grueso."
            if n > LAB_KLINE_LIMIT_MAX
            else None
        ),
        "binance_intervals": list(BINANCE_INTERVALS),
        "period_presets_days": {k: str(v) for k, v in PERIOD_PRESETS_DAYS.items()},
    }
