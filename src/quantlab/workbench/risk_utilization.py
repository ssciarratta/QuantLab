"""Risk utilization report — % used of max_qty / max_notional vs book (F69).

Compara exposición del ``PaperBook`` (posiciones abiertas) contra
``PaperRiskLimits``. Sin flip LIVE · sin place_order venue.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from quantlab.brokers.paper.book import PaperBook
from quantlab.brokers.paper.broker import PaperBroker
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.risk import PaperRiskLimits

_HUNDRED = Decimal("100")
_ZERO = Decimal("0")


def _as_str(value: Decimal) -> str:
    return str(value)


def _pct(used: Decimal, limit: Decimal) -> Decimal:
    """Porcentaje used/limit × 100 (0 si limit ≤ 0)."""
    if limit <= 0:
        return _ZERO
    return (used / limit) * _HUNDRED


def compute_risk_utilization(
    book: PaperBook,
    limits: PaperRiskLimits,
    *,
    mark_prices: dict[str, Decimal] | None = None,
    marks_source: str = "avg",
) -> dict[str, Any]:
    """Utilización qty/notional Decimal-safe vs límites paper.

    Convención:
    - ``used_qty`` = max |qty| entre posiciones abiertas (pico vs ``max_qty``)
    - ``used_notional`` = Σ |qty × mark| (exposición bruta vs ``max_notional``)
    - ``pct_*`` = used / limit × 100 (puede superar 100 si book > límite order)
    - por posición: qty, mark, notional, pct_qty, pct_notional
    """
    marks = dict(mark_prices or {})
    positions_out: list[dict[str, str]] = []
    used_qty = _ZERO
    used_notional = _ZERO

    for pos in book.get_positions():
        qty_abs = abs(Decimal(pos.quantity))
        avg = Decimal(pos.avg_price) if pos.avg_price is not None else _ZERO
        mark = marks.get(pos.symbol, avg)
        if pos.symbol not in marks:
            marks[pos.symbol] = mark
        notional_abs = qty_abs * abs(Decimal(mark))
        if qty_abs > used_qty:
            used_qty = qty_abs
        used_notional += notional_abs
        positions_out.append(
            {
                "symbol": pos.symbol,
                "qty": _as_str(Decimal(pos.quantity)),
                "avg_price": _as_str(avg),
                "mark": _as_str(Decimal(mark)),
                "notional": _as_str(notional_abs),
                "pct_qty": _as_str(_pct(qty_abs, limits.max_qty)),
                "pct_notional": _as_str(_pct(notional_abs, limits.max_notional)),
            }
        )

    pct_qty = _pct(used_qty, limits.max_qty)
    pct_notional = _pct(used_notional, limits.max_notional)
    allowed = (
        sorted(limits.allowed_symbols) if limits.allowed_symbols is not None else None
    )
    marks_out = {sym: _as_str(px) for sym, px in sorted(marks.items())}

    return {
        "ok": True,
        "kind": "risk_utilization",
        "limits": {
            "max_qty": _as_str(limits.max_qty),
            "max_notional": _as_str(limits.max_notional),
            "allowed_symbols": allowed,
        },
        "used": {
            "qty": _as_str(used_qty),
            "notional": _as_str(used_notional),
            "symbols": len(positions_out),
        },
        "pct": {
            "qty": _as_str(pct_qty),
            "notional": _as_str(pct_notional),
        },
        "positions": positions_out,
        "marks": marks_out,
        "marks_source": marks_source,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def utilization_from_broker(
    broker: PaperBroker,
    limits: PaperRiskLimits,
) -> dict[str, Any]:
    """Utilización con marks mid/last del MD subyacente del PaperBroker."""
    marks = broker.mark_prices()
    return compute_risk_utilization(
        broker.book, limits, mark_prices=marks, marks_source="broker"
    )


def utilization_from_book(
    book: PaperBook,
    limits: PaperRiskLimits,
) -> dict[str, Any]:
    """Utilización sin broker: marks = avg_price de cada posición."""
    return compute_risk_utilization(book, limits, mark_prices=None, marks_source="avg")
