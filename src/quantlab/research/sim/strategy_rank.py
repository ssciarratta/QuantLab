"""Ranking de estrategias sobre una sola moneda × mercados (research, sin LIVE).

Corre el universo runnable (sin demo dummy/buy_once), ordena por PnL % y
garantiza al menos una estrategia por familia; si hay más de ``top_n`` familias
con resultado OK, el ranking crece para incluirlas todas.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.research.sim.benchmark import compute_benchmark
from quantlab.research.sim.compare import (
    _UNCONSTRAINED_CASH_FLOOR,
    _UNCONSTRAINED_CASH_MULT,
    _apply_extra_costs_to_overlay,
    _bar_duration,
    _dec,
    _overlay_from_dict,
    _parse_extra_costs,
    _resolve_kline_limit,
)
from quantlab.research.sim.fee_schedules import (
    fee_model_from_schedule,
    get_fee_schedule,
    schedule_to_lab_fee_dict,
)
from quantlab.research.sim.leverage_overlay import LeverageOverlayConfig, apply_leverage_overlay
from quantlab.research.sim.sizing import (
    CAPITAL_MODES,
    build_margin_report,
    validate_trade_size,
)
from quantlab.research.sim.symbol_map import MARKET_TYPES, VENUES
from quantlab.workbench import lab_services
from quantlab.workbench.strategy_catalog import STRATEGY_CATALOG, StrategyMeta
from quantlab.workbench.strategy_guides import FAMILY_LABELS_ES

# Excluidas del ranking (demo / aprendizaje).
_RANK_EXCLUDE_IDS: frozenset[str] = frozenset({"dummy", "buy_once"})
_DEFAULT_TOP_N = 10


@dataclass(frozen=True, slots=True)
class RankCandidate:
    """Candidato OK para el ranking por mercado."""

    strategy_id: str
    strategy_name: str
    family: str
    family_label_es: str
    pnl: Decimal
    pnl_pct: Decimal
    payload: dict[str, Any]


def ranking_strategy_metas() -> list[StrategyMeta]:
    """Universo runnable del ranking (sin dummy / buy_once)."""
    return [
        m
        for m in STRATEGY_CATALOG
        if m.runnable and m.id not in _RANK_EXCLUDE_IDS
    ]


def select_diverse_top(
    candidates: list[RankCandidate],
    *,
    top_n: int = _DEFAULT_TOP_N,
) -> list[RankCandidate]:
    """Top por PnL % con ≥1 por familia; puede superar ``top_n`` si hay más familias.

    Orden de salida: PnL % descendente (empate → PnL absoluto).
    """
    if top_n < 1:
        raise ValidationError("top_n debe ser ≥ 1")
    if not candidates:
        return []

    def _sort_key(c: RankCandidate) -> tuple[Decimal, Decimal]:
        return (c.pnl_pct, c.pnl)

    ranked = sorted(candidates, key=_sort_key, reverse=True)

    best_by_family: dict[str, RankCandidate] = {}
    for c in ranked:
        if c.family not in best_by_family:
            best_by_family[c.family] = c

    selected: list[RankCandidate] = list(best_by_family.values())
    selected_ids = {c.strategy_id for c in selected}

    if len(selected) < top_n:
        for c in ranked:
            if c.strategy_id in selected_ids:
                continue
            selected.append(c)
            selected_ids.add(c.strategy_id)
            if len(selected) >= top_n:
                break

    return sorted(selected, key=_sort_key, reverse=True)


def _parse_pairs(request: dict[str, Any]) -> list[tuple[str, str]]:
    pairs_raw = request.get("pairs")
    if not isinstance(pairs_raw, list) or not pairs_raw:
        raise ValidationError(
            "pairs [{venue,underlying}] obligatorio (una sola moneda en N mercados)"
        )
    work: list[tuple[str, str]] = []
    for item in pairs_raw:
        if not isinstance(item, dict):
            raise ValidationError("pairs: cada item debe ser {venue, underlying}")
        v = str(item.get("venue", "")).strip().lower()
        u = str(item.get("underlying", "")).strip()
        if not v or not u:
            raise ValidationError("pairs: venue y underlying obligatorios")
        work.append((v, u))
    if len(work) > 20:
        raise ValidationError("demasiados pairs para ranking")
    return work


def _canonical_bases(work: list[tuple[str, str]]) -> set[str]:
    bases: set[str] = set()
    for _v, u in work:
        base = u.upper().replace("-", "").replace("/", "")
        for suffix in ("USDT", "USD", "USDC", "PERP"):
            if base.endswith(suffix) and len(base) > len(suffix):
                base = base[: -len(suffix)]
                break
        bases.add(base)
    return bases


def run_sim_strategy_rank(request: dict[str, Any]) -> dict[str, Any]:
    """Ranking multi-estrategia para una moneda × mercados marcados."""
    from quantlab.brokers.md_router import fetch_bars_for_instrument, fetch_funding_rates

    work = _parse_pairs(request)
    bases = _canonical_bases(work)
    if len(bases) != 1:
        raise ValidationError(
            "ranking requiere exactamente una moneda (mismo underlying) "
            f"en los pairs; bases detectadas: {sorted(bases)}"
        )
    coin = next(iter(bases))

    market_type = str(request.get("market_type", "futures")).strip().lower()
    if market_type not in MARKET_TYPES:
        raise ValidationError(f"market_type inválido: {market_type!r}")

    interval = str(request.get("interval", "1h"))
    period_days = request.get("period_days")
    kline_limit = request.get("kline_limit")
    capital_mode = str(request.get("capital_mode", "fixed")).strip().lower()
    if capital_mode not in CAPITAL_MODES:
        raise ValidationError(
            f"capital_mode inválido: {capital_mode!r}; "
            f"permitidos: {', '.join(CAPITAL_MODES)}"
        )
    per_trade_usd = _dec(request.get("per_trade_usd", "1000"), field="per_trade_usd")
    if capital_mode == "fixed":
        initial_capital = _dec(
            request.get("initial_capital", "100000"), field="initial_capital"
        )
        run_cash = initial_capital
    else:
        initial_capital = None
        run_cash = max(per_trade_usd * _UNCONSTRAINED_CASH_MULT, _UNCONSTRAINED_CASH_FLOOR)

    simulate_liquidation = bool(request.get("simulate_liquidation", True))
    apply_funding = bool(request.get("apply_funding", True))
    annual_bench_rate = _dec(
        request.get("annual_bench_rate", "0.05"), field="annual_bench_rate"
    )
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

    # Una sola x (el multi-x del panel no aplica al ranking).
    lev_raw = request.get("leverage", request.get("leverages"))
    if isinstance(lev_raw, list) and lev_raw:
        leverage = _dec(lev_raw[0], field="leverage")
    else:
        leverage = _dec(lev_raw if lev_raw is not None else "1", field="leverage")

    top_n = int(request.get("top_n", _DEFAULT_TOP_N))
    if top_n < 1:
        raise ValidationError("top_n debe ser ≥ 1")

    metas = ranking_strategy_metas()
    resolved_limit = _resolve_kline_limit(
        interval=interval,
        period_days=int(period_days) if period_days is not None else None,
        kline_limit=int(kline_limit) if kline_limit is not None else None,
    )

    markets: list[dict[str, Any]] = []

    for v, underlying in work:
        market_block: dict[str, Any] = {
            "venue": v,
            "market_label": v,
            "underlying": underlying,
            "ok": False,
            "error": None,
            "ranked": [],
            "n_strategies_run": 0,
            "n_strategies_ok": 0,
            "n_families_covered": 0,
        }
        if v not in VENUES:
            market_block["error"] = f"mercado desconocido: {v!r}"
            markets.append(market_block)
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
            market_block["error"] = str(exc)
            markets.append(market_block)
            continue

        duration = _bar_duration(bars)
        bench_capital = (
            initial_capital if initial_capital is not None else per_trade_usd
        )
        bench = compute_benchmark(bench_capital, annual_bench_rate, duration)

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

        sizing = validate_trade_size(
            initial_capital if initial_capital is not None else run_cash,
            per_trade_usd,
            leverage,
            market_type=market_type,
            capital_mode=capital_mode,
        )
        if not sizing["ok"]:
            market_block["error"] = "; ".join(sizing["errors"])
            markets.append(market_block)
            continue

        funding_rates: list[Decimal] | None = None
        if apply_funding and market_type == "futures":
            funding_rates = fetch_funding_rates(resolved, limit=len(bars))

        candidates: list[RankCandidate] = []
        n_run = 0
        for meta in metas:
            n_run += 1
            try:
                bt = lab_services.run_lab_backtest(
                    strategy_id=meta.id,
                    params=None,
                    bars=bars,
                    instrument_id=resolved.instrument_id,
                    data_source=f"{v}_{market_type}",
                    initial_cash=run_cash,
                    experiment_id=f"sim-rank-{v}-{resolved.underlying}-{meta.id}",
                    fee_model=fee_model,
                    fee_schedule_meta=fee_meta,
                )
            except ValidationError:
                continue

            margin_report = build_margin_report(
                capital_mode=capital_mode,
                initial_capital=initial_capital,
                per_trade=per_trade_usd,
                leverage=leverage,
                market_type=market_type,
                fills=bt.get("fills") if isinstance(bt.get("fills"), list) else [],
            )
            overlay_raw = apply_leverage_overlay(
                bt,
                config=LeverageOverlayConfig(
                    leverage=leverage,
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
            fam_label = FAMILY_LABELS_ES.get(meta.family, meta.family)
            payload = {
                "venue": v,
                "market_type": market_type,
                "underlying": resolved.underlying,
                "instrument_id": resolved.instrument_id,
                "leverage": str(leverage),
                "strategy_id": meta.id,
                "strategy_name": meta.name,
                "family": meta.family,
                "family_label_es": fam_label,
                "ok": True,
                "overlay": overlay.to_dict(),
                "backtest": {
                    **bt,
                    "fee_schedule_venue": fee_sched.to_dict(),
                    "benchmark": bench.to_dict(),
                    "sizing": sizing,
                    "margin_report": margin_report,
                    "capital_mode": capital_mode,
                    "display_initial_capital": (
                        str(initial_capital) if initial_capital is not None else None
                    ),
                    "margin_per_trade": margin_report["margin_per_trade"],
                    "peak_margin": margin_report["peak_margin"],
                },
                "error": None,
            }
            candidates.append(
                RankCandidate(
                    strategy_id=meta.id,
                    strategy_name=meta.name,
                    family=meta.family,
                    family_label_es=fam_label,
                    pnl=overlay.pnl,
                    pnl_pct=overlay.pnl_pct,
                    payload=payload,
                )
            )

        selected = select_diverse_top(candidates, top_n=top_n)
        market_block.update(
            {
                "ok": True,
                "underlying": resolved.underlying,
                "instrument_id": resolved.instrument_id,
                "ranked": [
                    {**c.payload, "rank": i + 1} for i, c in enumerate(selected)
                ],
                "n_strategies_run": n_run,
                "n_strategies_ok": len(candidates),
                "n_families_covered": len({c.family for c in selected}),
            }
        )
        markets.append(market_block)

    return {
        "ok": any(m.get("ok") for m in markets),
        "kind": "sim_strategy_rank",
        "coin": coin,
        "markets": markets,
        "common": {
            "market_type": market_type,
            "interval": interval,
            "kline_limit": resolved_limit,
            "capital_mode": capital_mode,
            "initial_capital": str(initial_capital) if initial_capital is not None else None,
            "run_cash": str(run_cash),
            "per_trade_usd": str(per_trade_usd),
            "leverage": str(leverage),
            "annual_bench_rate": str(annual_bench_rate),
            "simulate_liquidation": simulate_liquidation,
            "apply_funding": apply_funding,
            "top_n": top_n,
            "n_strategies_universe": len(metas),
            "excluded_strategy_ids": sorted(_RANK_EXCLUDE_IDS),
            "extra_costs": [c.to_dict() for c in extra_costs],
            "maker_bps_override": str(maker_bps_override)
            if maker_bps_override is not None
            else None,
            "taker_bps_override": str(taker_bps_override)
            if taker_bps_override is not None
            else None,
            "note": (
                "Ranking por PnL % · ≥1 por familia · puede superar top_n "
                "si hay más familias con resultado OK. LIVE bloqueado."
            ),
        },
        "live_blocked": LIVE_BLOCKED is True,
    }
