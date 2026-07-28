"""Orquestador de comparación multi-venue (research, sin LIVE)."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.brokers.md_limits import LAB_KLINE_LIMIT_MAX, LAB_KLINE_LIMIT_MIN
from quantlab.brokers.md_router import fetch_bars_for_instrument, fetch_funding_rates
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.research.sim.benchmark import compute_benchmark
from quantlab.research.sim.costs import ExtraCost, apply_extra_costs
from quantlab.research.sim.fee_schedules import (
    fee_model_from_schedule,
    get_fee_schedule,
    schedule_to_lab_fee_dict,
)
from quantlab.research.sim.leverage_overlay import LeverageOverlayConfig, apply_leverage_overlay
from quantlab.research.sim.models import SimCompareRow, SimOverlayResult
from quantlab.research.sim.sizing import validate_trade_size
from quantlab.research.sim.symbol_map import MARKET_TYPES, VENUES
from quantlab.workbench import lab_services

_MAX_UNDERLYINGS = 5
_INTERVAL_RE = re.compile(r"^(\d+)([mhd])$", re.IGNORECASE)


def _dec(raw: Any, *, field: str) -> Decimal:
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field} decimal inválido: {raw!r}") from exc


def _parse_extra_costs(raw: Sequence[dict[str, Any]] | None) -> list[ExtraCost]:
    if not raw:
        return []
    out: list[ExtraCost] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValidationError("extra_costs: cada item debe ser dict")
        kind = str(item.get("kind", "")).strip()
        if kind not in ("fixed_usd", "percent_notional"):
            raise ValidationError(f"extra_cost kind inválido: {kind!r}")
        out.append(
            ExtraCost(
                name=str(item.get("name", "extra")),
                kind=kind,  # type: ignore[arg-type]
                amount=_dec(item.get("amount", "0"), field="extra_cost.amount"),
            )
        )
    return out


def _interval_hours(interval: str) -> Decimal:
    from quantlab.research.sim.period_bars import interval_minutes

    mins = interval_minutes(interval)
    return mins / Decimal("60")


def _resolve_kline_limit(
    *,
    interval: str,
    period_days: int | None,
    kline_limit: int | None,
) -> int:
    if kline_limit is not None:
        return int(kline_limit)
    if period_days is not None:
        hours = Decimal(str(period_days)) * Decimal("24")
        bar_hours = _interval_hours(interval)
        limit = math.ceil(float(hours / bar_hours))
        return max(LAB_KLINE_LIMIT_MIN, min(limit, LAB_KLINE_LIMIT_MAX))
    return 24


def _bar_duration(bars: list[Bar]) -> timedelta:
    if not bars:
        return timedelta(0)
    start = bars[0].timestamp_open
    end = bars[-1].timestamp_close
    return end - start


def _overlay_from_dict(raw: dict[str, Any]) -> SimOverlayResult:
    curve_raw = raw.get("equity_curve") or []
    curve = tuple(
        (str(p["ts"]), str(p["equity"]))
        for p in curve_raw
        if isinstance(p, dict) and p.get("ts") is not None
    )
    return SimOverlayResult(
        initial_equity=_dec(raw["initial_equity"], field="overlay.initial_equity"),
        final_equity=_dec(raw["final_equity"], field="overlay.final_equity"),
        pnl=_dec(raw["pnl"], field="overlay.pnl"),
        pnl_pct=_dec(raw["pnl_pct"], field="overlay.pnl_pct"),
        leverage=_dec(raw["leverage"], field="overlay.leverage"),
        liquidated=bool(raw.get("liquidated")),
        liquidation_bar_index=raw.get("liquidation_bar_index"),
        total_funding=_dec(raw.get("total_funding", "0"), field="overlay.total_funding"),
        funding_applied=bool(raw.get("funding_applied")),
        liquidation_simulated=bool(raw.get("liquidation_simulated")),
        equity_curve=curve,
    )


def _apply_extra_costs_to_overlay(
    overlay_raw: dict[str, Any],
    *,
    costs: list[ExtraCost],
    notional: Decimal,
) -> dict[str, Any]:
    if not costs:
        return overlay_raw
    extra = apply_extra_costs(costs=costs, notional=notional)
    if extra <= Decimal("0"):
        return overlay_raw
    initial = _dec(overlay_raw["initial_equity"], field="initial_equity")
    final = _dec(overlay_raw["final_equity"], field="final_equity") - extra
    pnl = final - initial
    pnl_pct = (pnl / initial * Decimal("100")) if initial else Decimal("0")
    out = dict(overlay_raw)
    out["final_equity"] = str(final)
    out["pnl"] = str(pnl)
    out["pnl_pct"] = str(pnl_pct)
    out["extra_costs_total"] = str(extra)
    return out


def run_sim_compare(request: dict[str, Any]) -> dict[str, Any]:
    """Compara backtest + overlay leverage por venue×underlying×leverage.

    Acepta ``pairs: [{venue, underlying}, ...]`` (preferido UI) o el producto
    cartesiano ``venues`` × ``underlyings``.
    """
    pairs_raw = request.get("pairs")
    work: list[tuple[str, str]] = []
    if isinstance(pairs_raw, list) and pairs_raw:
        for item in pairs_raw:
            if not isinstance(item, dict):
                raise ValidationError("pairs: cada item debe ser {venue, underlying}")
            v = str(item.get("venue", "")).strip().lower()
            u = str(item.get("underlying", "")).strip()
            if not v or not u:
                raise ValidationError("pairs: venue y underlying obligatorios")
            work.append((v, u))
        if len(work) > _MAX_UNDERLYINGS * 4:
            raise ValidationError("demasiados pairs")
    else:
        venues_raw = request.get("venues") or []
        underlyings_raw = request.get("underlyings") or []
        if not venues_raw or not underlyings_raw:
            raise ValidationError(
                "venues+underlyings u pairs [{venue,underlying}] son obligatorios"
            )
        underlyings = [str(u).strip() for u in underlyings_raw[:_MAX_UNDERLYINGS]]
        if len(underlyings_raw) > _MAX_UNDERLYINGS:
            raise ValidationError(f"máximo {_MAX_UNDERLYINGS} underlyings")
        for venue in venues_raw:
            for underlying in underlyings:
                work.append((str(venue).strip().lower(), underlying))

    market_type = str(request.get("market_type", "futures")).strip().lower()
    if market_type not in MARKET_TYPES:
        raise ValidationError(f"market_type inválido: {market_type!r}")

    strategy_id = str(request.get("strategy_id", "momentum"))
    params = request.get("params")
    interval = str(request.get("interval", "1h"))
    period_days = request.get("period_days")
    kline_limit = request.get("kline_limit")
    initial_capital = _dec(request.get("initial_capital", "100000"), field="initial_capital")
    per_trade_usd = _dec(request.get("per_trade_usd", "1000"), field="per_trade_usd")
    simulate_liquidation = bool(request.get("simulate_liquidation", True))
    apply_funding = bool(request.get("apply_funding", True))
    annual_bench_rate = _dec(request.get("annual_bench_rate", "0.05"), field="annual_bench_rate")
    extra_costs = _parse_extra_costs(request.get("extra_costs"))
    maker_bps_override = (
        _dec(request["maker_bps"], field="maker_bps")
        if request.get("maker_bps") is not None
        else None
    )
    taker_bps_override = (
        _dec(request["taker_bps"], field="taker_bps")
        if request.get("taker_bps") is not None
        else None
    )

    leverages_raw = request.get("leverages") or [Decimal("1")]
    leverages: list[Decimal] = [_dec(x, field="leverage") for x in leverages_raw]

    resolved_limit = _resolve_kline_limit(
        interval=interval,
        period_days=int(period_days) if period_days is not None else None,
        kline_limit=int(kline_limit) if kline_limit is not None else None,
    )

    rows: list[SimCompareRow] = []
    bench_by_key: dict[str, dict[str, Any]] = {}

    for v, underlying in work:
        if v not in VENUES:
            for lev in leverages:
                rows.append(
                    SimCompareRow(
                        venue=v,
                        market_type=market_type,
                        underlying=underlying,
                        instrument_id="",
                        leverage=lev,
                        strategy_id=strategy_id,
                        ok=False,
                        error=f"venue desconocido: {v!r}",
                    )
                )
            continue

        try:
            resolved, bars = fetch_bars_for_instrument(
                underlying,
                venue=v,
                market_type=market_type,
                interval=interval,
                kline_limit=resolved_limit,
            )
        except ValidationError as exc:
            for lev in leverages:
                rows.append(
                    SimCompareRow(
                        venue=v,
                        market_type=market_type,
                        underlying=underlying,
                        instrument_id="",
                        leverage=lev,
                        strategy_id=strategy_id,
                        ok=False,
                        error=str(exc),
                    )
                )
            continue

        duration = _bar_duration(bars)
        bench = compute_benchmark(initial_capital, annual_bench_rate, duration)
        bench_by_key[f"{v}:{resolved.underlying}"] = bench.to_dict()

        fee_sched = get_fee_schedule(v, market_type)
        if maker_bps_override is not None or taker_bps_override is not None:
            fee_sched = type(fee_sched)(
                venue=fee_sched.venue,
                market_type=fee_sched.market_type,
                maker_bps=maker_bps_override
                if maker_bps_override is not None
                else fee_sched.maker_bps,
                taker_bps=taker_bps_override
                if taker_bps_override is not None
                else fee_sched.taker_bps,
                notes=fee_sched.notes + " (override UI)",
                source_url=fee_sched.source_url,
            )

        fee_model = fee_model_from_schedule(fee_sched)
        fee_meta = schedule_to_lab_fee_dict(fee_sched)

        for lev in leverages:
                sizing = validate_trade_size(
                    initial_capital,
                    per_trade_usd,
                    lev,
                    market_type=market_type,
                )
                if not sizing["ok"]:
                    rows.append(
                        SimCompareRow(
                            venue=v,
                            market_type=market_type,
                            underlying=resolved.underlying,
                            instrument_id=resolved.instrument_id,
                            leverage=lev,
                            strategy_id=strategy_id,
                            ok=False,
                            error="; ".join(sizing["errors"]),
                        )
                    )
                    continue

                try:
                    bt = lab_services.run_lab_backtest(
                        strategy_id=strategy_id,
                        params=params if isinstance(params, dict) else None,
                        bars=bars,
                        instrument_id=resolved.instrument_id,
                        data_source=f"{v}_{market_type}",
                        initial_cash=initial_capital,
                        experiment_id=f"sim-compare-{v}-{resolved.underlying}-{lev}",
                        fee_model=fee_model,
                        fee_schedule_meta=fee_meta,
                    )
                except ValidationError as exc:
                    rows.append(
                        SimCompareRow(
                            venue=v,
                            market_type=market_type,
                            underlying=resolved.underlying,
                            instrument_id=resolved.instrument_id,
                            leverage=lev,
                            strategy_id=strategy_id,
                            ok=False,
                            error=str(exc),
                        )
                    )
                    continue

                funding_rates: list[Decimal] | None = None
                if apply_funding and market_type == "futures":
                    funding_rates = fetch_funding_rates(resolved, limit=len(bars))

                overlay_raw = apply_leverage_overlay(
                    bt,
                    config=LeverageOverlayConfig(
                        leverage=lev,
                        simulate_liquidation=simulate_liquidation,
                        apply_funding=apply_funding,
                    ),
                    funding_rates=funding_rates,
                )
                notional = _dec(sizing["notional"], field="notional")
                overlay_raw = _apply_extra_costs_to_overlay(
                    overlay_raw,
                    costs=extra_costs,
                    notional=notional,
                )
                overlay = _overlay_from_dict(overlay_raw)

                rows.append(
                    SimCompareRow(
                        venue=v,
                        market_type=market_type,
                        underlying=resolved.underlying,
                        instrument_id=resolved.instrument_id,
                        leverage=lev,
                        strategy_id=strategy_id,
                        ok=True,
                        overlay=overlay,
                        backtest={
                            **bt,
                            "fee_schedule_venue": fee_sched.to_dict(),
                            "benchmark": bench.to_dict(),
                            "sizing": sizing,
                        },
                    )
                )

    return {
        "ok": all(r.ok for r in rows) if rows else False,
        "rows": [r.to_dict() for r in rows],
        "common": {
            "strategy_id": strategy_id,
            "market_type": market_type,
            "interval": interval,
            "kline_limit": resolved_limit,
            "initial_capital": str(initial_capital),
            "per_trade_usd": str(per_trade_usd),
            "annual_bench_rate": str(annual_bench_rate),
            "simulate_liquidation": simulate_liquidation,
            "apply_funding": apply_funding,
            "extra_costs": [c.to_dict() for c in extra_costs],
            "benchmarks_by_key": bench_by_key,
            "maker_bps_override": str(maker_bps_override)
            if maker_bps_override is not None
            else None,
            "taker_bps_override": str(taker_bps_override)
            if taker_bps_override is not None
            else None,
            "fee_fills_note": (
                "fills usan MakerTakerFeeModel del schedule venue "
                "(bar-based 5A cobra siempre taker_bps)"
            ),
        },
        "live_blocked": LIVE_BLOCKED is True,
    }
