"""Validadores de calidad de datos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from quantlab.core.types.market import Bar, Trade


class QualitySeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass(frozen=True, slots=True)
class QualityIssue:
    code: str
    severity: QualitySeverity
    message: str


@dataclass(frozen=True, slots=True)
class QualityReport:
    issues: tuple[QualityIssue, ...]

    @property
    def has_fatal(self) -> bool:
        return any(i.severity is QualitySeverity.FATAL for i in self.issues)

    @property
    def has_error(self) -> bool:
        return any(i.severity is QualitySeverity.ERROR for i in self.issues)


def validate_trades(trades: list[Trade]) -> QualityReport:
    issues: list[QualityIssue] = []
    prev_by_inst: dict[str, datetime] = {}
    seen_ts: set[tuple[str, datetime]] = set()
    seen_ids: set[str] = set()
    for trade in trades:
        if trade.timestamp.tzinfo is None:
            issues.append(QualityIssue("naive_timestamp", QualitySeverity.FATAL, "timestamp naive"))
        if trade.price <= 0:
            issues.append(QualityIssue("non_positive_price", QualitySeverity.ERROR, "price<=0"))
        if trade.quantity <= 0:
            issues.append(QualityIssue("non_positive_qty", QualitySeverity.ERROR, "qty<=0"))
        prev = prev_by_inst.get(trade.instrument_id)
        if prev is not None and trade.timestamp < prev:
            issues.append(
                QualityIssue("out_of_order", QualitySeverity.ERROR, "timestamp no monótono")
            )
        ts_key = (trade.instrument_id, trade.timestamp)
        if ts_key in seen_ts:
            issues.append(
                QualityIssue("duplicate_timestamp", QualitySeverity.ERROR, "timestamp duplicado")
            )
        seen_ts.add(ts_key)
        if trade.trade_id in seen_ids:
            issues.append(QualityIssue("duplicate", QualitySeverity.WARNING, "trade_id duplicado"))
        seen_ids.add(trade.trade_id)
        prev_by_inst[trade.instrument_id] = trade.timestamp
    return QualityReport(tuple(issues))


def validate_bars(bars: list[Bar]) -> QualityReport:
    issues: list[QualityIssue] = []
    prev_close_by_inst: dict[str, datetime] = {}
    seen_open: set[tuple[str, datetime]] = set()
    zero = Decimal("0")
    for bar in bars:
        if bar.timestamp_open.tzinfo is None or bar.timestamp_close.tzinfo is None:
            issues.append(
                QualityIssue("naive_bar_ts", QualitySeverity.FATAL, "bar timestamp naive")
            )
        if bar.volume < zero:
            issues.append(QualityIssue("negative_volume", QualitySeverity.ERROR, "volume<0"))
        if bar.high < max(bar.open, bar.close):
            issues.append(
                QualityIssue("ohlc_high", QualitySeverity.ERROR, "high < max(open, close)")
            )
        if bar.low > min(bar.open, bar.close):
            issues.append(QualityIssue("ohlc_low", QualitySeverity.ERROR, "low > min(open, close)"))
        if bar.high < bar.low:
            issues.append(QualityIssue("ohlc_range", QualitySeverity.ERROR, "high < low"))
        if bar.volume == zero:
            issues.append(QualityIssue("empty_bar", QualitySeverity.INFO, "barra sin volumen"))
        open_key = (bar.instrument_id, bar.timestamp_open)
        if open_key in seen_open:
            issues.append(
                QualityIssue(
                    "duplicate_timestamp",
                    QualitySeverity.ERROR,
                    "timestamp_open duplicado",
                )
            )
        seen_open.add(open_key)
        prev_close = prev_close_by_inst.get(bar.instrument_id)
        if prev_close is not None and bar.timestamp_close <= prev_close:
            issues.append(
                QualityIssue(
                    "out_of_order",
                    QualitySeverity.ERROR,
                    "timestamp_close no ascendente",
                )
            )
        prev_close_by_inst[bar.instrument_id] = bar.timestamp_close
    return QualityReport(tuple(issues))


def sanitize_bars(bars: list[Bar]) -> tuple[list[Bar], QualityReport]:
    """Descarta barras con timestamps duplicados o desordenados; reporta issues."""
    issues: list[QualityIssue] = []
    kept: list[Bar] = []
    seen_open: set[tuple[str, datetime]] = set()
    last_close_by_inst: dict[str, datetime] = {}
    for bar in bars:
        key = (bar.instrument_id, bar.timestamp_open)
        if key in seen_open:
            issues.append(
                QualityIssue(
                    "duplicate_timestamp",
                    QualitySeverity.WARNING,
                    f"descartada barra duplicada {bar.timestamp_open.isoformat()}",
                )
            )
            continue
        last_close = last_close_by_inst.get(bar.instrument_id)
        if last_close is not None and bar.timestamp_close <= last_close:
            issues.append(
                QualityIssue(
                    "out_of_order",
                    QualitySeverity.WARNING,
                    f"descartada barra desordenada {bar.timestamp_open.isoformat()}",
                )
            )
            continue
        seen_open.add(key)
        last_close_by_inst[bar.instrument_id] = bar.timestamp_close
        kept.append(bar)
    ohlcv = validate_bars(kept)
    return kept, QualityReport(tuple(issues) + ohlcv.issues)
