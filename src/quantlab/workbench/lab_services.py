"""Adapters thin del laboratorio para el workbench (research-safe, sin LIVE).

Usa datos sintéticos en memoria / registry temporal. Nunca envía órdenes live.
"""

from __future__ import annotations

import contextlib
import re
import tempfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from quantlab.backtester import BarBacktestConfig, BarBacktester
from quantlab.brokers.binance.fees import (
    binance_spot_fee_model,
    resolve_binance_spot_fee_schedule,
)
from quantlab.brokers.md_limits import (
    LAB_KLINE_HEAVY_WARN,
    LAB_KLINE_LIMIT_MAX,
    LAB_KLINE_LIMIT_MIN,
)
from quantlab.core.exceptions import ValidationError
from quantlab.core.types.enums import ExperimentStatus
from quantlab.core.types.manifests import ExecutionModelVersions, ExperimentManifest
from quantlab.core.types.market import Bar
from quantlab.core.types.results import SimulationResult
from quantlab.core.types.serialization import dataclass_to_dict, to_jsonable
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.execution_export.hummingbot import ExecutionPackage, HummingbotExporter
from quantlab.experiments.registry import ExperimentRegistry
from quantlab.features.pipeline import build_pipeline
from quantlab.features.serialization import feature_frame_to_dict
from quantlab.features.store import FeatureStore
from quantlab.features.transformers import (
    ClosePriceTransformer,
    LogReturnTransformer,
    SimpleReturnTransformer,
)
from quantlab.montecarlo.simulator import MonteCarloSimulator
from quantlab.optimizer.grid import GridSearchOptimizer
from quantlab.optimizer.pareto import pareto_from_trials
from quantlab.research.alpha import AlphaScanner
from quantlab.research.strategies.buy_once import BuyOnceStrategy
from quantlab.research.strategies.simple_momentum import SimpleMomentumStrategy
from quantlab.validation.leakage import check_temporal_leakage
from quantlab.validation.splits import train_val_oos_split, walk_forward
from quantlab.workbench.montecarlo_runs import persist_montecarlo_run
from quantlab.workbench.optimizer_runs import persist_optimizer_run
from quantlab.workbench.strategy_catalog import (
    CANONICAL_STRATEGY_IDS,
    build_strategy,
    is_mm_strategy,
    list_strategy_catalog,
    list_strategy_ids,
    maybe_wrap_for_bar_backtest,
    merge_default_params,
    normalize_strategy_id,
)
from quantlab.workbench.validation_runs import persist_validation_run

STRATEGY_IDS: tuple[str, ...] = CANONICAL_STRATEGY_IDS

# Fail-closed path segment / export filename (F25 M1).
_EXPERIMENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_experiment_id(experiment_id: str) -> str:
    """Valida ``experiment_id`` charset ``^[A-Za-z0-9_-]+$`` (sin path separators)."""
    if not isinstance(experiment_id, str):
        raise ValidationError(f"experiment_id inválido (tipo): {type(experiment_id).__name__}")
    eid = experiment_id.strip()
    if not eid or not _EXPERIMENT_ID_RE.fullmatch(eid):
        raise ValidationError(
            f"experiment_id inválido (charset ^[A-Za-z0-9_-]+$): {experiment_id!r}"
        )
    return eid


CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "id": "backtest",
        "label": "Backtest bar-based",
        "method": "POST",
        "path": "/api/lab/backtest",
    },
    {"id": "scanner", "label": "Alpha Scanner", "method": "POST", "path": "/api/lab/scanner"},
    {
        "id": "metrics",
        "label": "Último resultado / metrics",
        "method": "GET",
        "path": "/api/lab/metrics",
    },
    {
        "id": "experiments",
        "label": "Experiment Registry",
        "method": "GET",
        "path": "/api/lab/experiments",
    },
    {
        "id": "optimize",
        "label": "Optimizer grid + Pareto (mini)",
        "method": "POST",
        "path": "/api/lab/optimize",
    },
    {
        "id": "optimize_history",
        "label": "Optimizer history (session)",
        "method": "GET",
        "path": "/api/lab/optimize/history",
    },
    {
        "id": "montecarlo",
        "label": "Monte Carlo (mini)",
        "method": "POST",
        "path": "/api/lab/montecarlo",
    },
    {
        "id": "montecarlo_history",
        "label": "Monte Carlo history (session)",
        "method": "GET",
        "path": "/api/lab/montecarlo/history",
    },
    {
        "id": "montecarlo_delete",
        "label": "Delete Monte Carlo run",
        "method": "DELETE",
        "path": "/api/lab/montecarlo/history/{run_id}",
    },
    {
        "id": "features",
        "label": "Features pipeline demo",
        "method": "POST",
        "path": "/api/lab/features/run",
    },
    {
        "id": "features_store",
        "label": "Feature Store browser",
        "method": "GET",
        "path": "/api/lab/features/store",
    },
    {
        "id": "export_hb",
        "label": "Hummingbot export",
        "method": "POST",
        "path": "/api/lab/export-hb",
    },
    {
        "id": "exports",
        "label": "Hummingbot exports (session)",
        "method": "GET",
        "path": "/api/lab/exports",
    },
    {
        "id": "validation",
        "label": "Validation / Walk-Forward runner",
        "method": "POST",
        "path": "/api/lab/validation/run",
    },
    {
        "id": "validation_list",
        "label": "Validation runs (session)",
        "method": "GET",
        "path": "/api/lab/validation",
    },
    {
        "id": "strategies",
        "label": "Strategy catalog",
        "method": "GET",
        "path": "/api/lab/strategies",
    },
    {
        "id": "reports",
        "label": "Reports / Metrics history",
        "method": "GET",
        "path": "/api/lab/reports",
    },
    {"id": "health", "label": "Health / Mode", "method": "GET", "path": "/api/health"},
    {"id": "market", "label": "Market Data", "method": "GET", "path": "/api/broker/snapshot"},
    {"id": "blotter", "label": "Paper Blotter", "method": "POST", "path": "/api/paper/submit"},
)


def make_synthetic_bars(
    n: int = 24,
    *,
    instrument_id: str = "WB:SYN",
    start_price: int = 100,
    drift: int = 1,
) -> list[Bar]:
    """Barras 1m sintéticas deterministas (sin red / credenciales)."""
    if n < 1:
        raise ValidationError("n_bars >= 1")
    out: list[Bar] = []
    base = datetime(2024, 6, 1, tzinfo=UTC)
    for i in range(n):
        c = Decimal(start_price + drift * i)
        t0 = base + timedelta(minutes=i)
        out.append(
            Bar(
                instrument_id=instrument_id,
                open=c,
                high=c + Decimal("1"),
                low=c - Decimal("1"),
                close=c,
                volume=Decimal("100") + Decimal(i),
                timestamp_open=t0,
                timestamp_close=t0 + timedelta(minutes=1),
                timeframe="1m",
            )
        )
    return out


def make_scanner_universe() -> dict[str, list[Bar]]:
    """Universo mínimo multi-instrumento para Alpha Scanner."""
    return {
        "WB:A": make_synthetic_bars(16, instrument_id="WB:A", start_price=100, drift=1),
        "WB:B": make_synthetic_bars(16, instrument_id="WB:B", start_price=50, drift=2),
        "WB:C": make_synthetic_bars(16, instrument_id="WB:C", start_price=200, drift=0),
    }


def _build_strategy(strategy_id: str, params: dict[str, Any]) -> Any:
    return build_strategy(strategy_id, params)


def _backtest_verdict(
    *,
    strategy_id: str,
    n_fills: int,
    n_orders: int,
    n_bars: int,
    data_source: str,
) -> tuple[str, str]:
    """Mensaje corto para UI: qué pasó en el backtest."""
    if n_fills > 0:
        return (
            "traded",
            f"OK: {n_fills} fill(s) en {n_bars} barras ({data_source}). "
            f"Equity cambia según PnL simulado; no es orden real.",
        )
    if n_orders > 0:
        return (
            "quoted_no_fill",
            f"La estrategia emitió {n_orders} orden(es) LIMIT pero ninguna tocó el OHLC "
            f"de la barra (fills=0). Equity queda en capital inicial. "
            f"Probá más velas, interval más chico, o estrategia direccional (momentum/ema).",
        )
    mm = is_mm_strategy(strategy_id)
    if mm:
        return (
            "no_orders_mm",
            "Market making no llegó a cotizar (o cotizó inválido). "
            "En alts baratas un spread fijo grande deja fills=0. "
            "Re-corré el pipeline (fix aplicado) o probá momentum/rsi_momentum.",
        )
    return (
        "no_signal",
        f"Sin órdenes ni fills en {n_bars} barras: la señal no disparó entrada. "
        "Subí n_bars/klines o cambió de estrategia (p. ej. momentum, breakout).",
    )


def _serialize_trade_detail(
    result: Any,
    *,
    max_rows: int = 2000,
) -> dict[str, Any]:
    """Fills + órdenes del simulador para UI/Reports (detalle, no solo resumen)."""
    sim = result.simulation
    order_by_id = {o.order_id: o for o in sim.orders}
    fills_out: list[dict[str, Any]] = []
    for f in sim.fills[:max_rows]:
        ord_ = order_by_id.get(f.order_id)
        fills_out.append(
            {
                "fill_id": f.fill_id,
                "order_id": f.order_id,
                "instrument_id": f.instrument_id,
                "side": (
                    ord_.side.value
                    if ord_ is not None
                    else getattr(getattr(f, "side", None), "value", None)
                ),
                "price": str(f.price),
                "quantity": str(f.quantity),
                "fee": str(f.fee.amount),
                "fee_currency": f.fee.currency,
                "liquidity": f.liquidity.value,
                "timestamp": f.timestamp.isoformat(),
            }
        )
    orders_out: list[dict[str, Any]] = []
    for o in sim.orders[:max_rows]:
        orders_out.append(
            {
                "order_id": o.order_id,
                "client_order_id": o.client_order_id,
                "instrument_id": o.instrument_id,
                "side": o.side.value,
                "order_type": o.order_type.value,
                "quantity": str(o.quantity),
                "filled_quantity": str(o.filled_quantity),
                "price": str(o.price) if o.price is not None else None,
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
            }
        )
    equity_tail = [
        {"ts": p.timestamp.isoformat(), "equity": str(p.equity)}
        for p in sim.equity_curve[-200:]
    ]
    return {
        "fills": fills_out,
        "orders": orders_out,
        "fills_truncated": len(fills_out) < len(sim.fills),
        "orders_truncated": len(orders_out) < len(sim.orders),
        "equity_curve_tail": equity_tail,
    }


def run_lab_backtest(
    *,
    strategy_id: str = "momentum",
    params: dict[str, Any] | None = None,
    n_bars: int = 24,
    bars: list[Bar] | None = None,
    instrument_id: str | None = None,
    data_source: str = "synthetic",
    experiment_id: str = "wb-lab-backtest",
    reports_dir: Path | None = None,
    initial_cash: Decimal | None = None,
    fee_model: Any | None = None,
    fee_schedule_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Corre BarBacktester 5A sobre barras sintéticas o ``bars`` provistas.

    Si ``reports_dir`` está set, persiste MetricsResult/summary (+ HTML) en
    sesión (F29 Report Viewer / Metrics History).

    ``fee_model`` opcional: si None, Binance Spot VIP0 (comportamiento histórico).
    ``fee_schedule_meta`` alinea fee_schedule/fee_per_side del summary con el model.
    """
    experiment_id = validate_experiment_id(experiment_id)
    sid = normalize_strategy_id(strategy_id)
    # Lab backtest: momentum default lookback=2 (histórico F21) si no viene en params.
    caller = dict(params or {})
    if sid == "momentum" and "lookback" not in caller:
        caller["lookback"] = 2
    strategy_params = merge_default_params(sid, caller)

    if bars is not None:
        if len(bars) < 4:
            raise ValidationError("bars requiere al menos 4 barras")
        run_bars = bars
        src = data_source
        iid = instrument_id or (bars[0].instrument_id if bars else None)
        n_used = len(run_bars)
    else:
        if n_bars < 4 or n_bars > 2000:
            raise ValidationError("n_bars debe estar entre 4 y 2000")
        run_bars = make_synthetic_bars(n_bars)
        src = "synthetic"
        iid = run_bars[0].instrument_id if run_bars else None
        n_used = n_bars

    strategy = maybe_wrap_for_bar_backtest(sid, _build_strategy(sid, strategy_params))
    if fee_model is None:
        fee_schedule = resolve_binance_spot_fee_schedule()
        fee_model = binance_spot_fee_model()
        fee_dict = fee_schedule.to_dict()
    else:
        if fee_schedule_meta is not None:
            fee_dict = dict(fee_schedule_meta)
        else:
            fee_dict = {
                "schedule_id": getattr(fee_model, "model_id", "custom"),
                "as_of": "",
                "source_url": "",
                "maker_bps": str(getattr(fee_model, "maker_bps", "")),
                "taker_bps": str(getattr(fee_model, "taker_bps", "")),
                "maker_pct": "",
                "taker_pct": "",
                "use_bnb_discount": False,
                "note": "fee_model custom",
            }
    if initial_cash is None:
        initial_cash = Decimal("100000")
    elif initial_cash <= Decimal("0"):
        raise ValidationError("initial_cash debe ser > 0")
    bt = BarBacktester(
        BarBacktestConfig(experiment_id=experiment_id, initial_cash=initial_cash),
        fee_model=fee_model,
    )
    result = bt.run(strategy, run_bars)
    n_fills = len(result.simulation.fills)
    # El motor solo materializa Order al fill; contar PLACE en el log para UI honesta.
    n_orders = sum(
        1
        for e in result.simulation.events_log
        if isinstance(e, dict) and e.get("intent_type") == "place_order"
    )
    if n_orders == 0:
        n_orders = len(result.simulation.orders)
    final_eq = (
        result.simulation.equity_curve[-1].equity
        if result.simulation.equity_curve
        else Decimal("0")
    )
    total_fees = result.accounting.total_fees
    avg_fee_per_fill = (total_fees / n_fills) if n_fills > 0 else None
    detail = _serialize_trade_detail(result)
    bar_range: dict[str, Any] | None = None
    if run_bars:
        bar_range = {
            "start": run_bars[0].timestamp_open.isoformat(),
            "end": run_bars[-1].timestamp_close.isoformat(),
            "n_bars": len(run_bars),
            "interval": run_bars[0].timeframe,
        }
    verdict, verdict_es = _backtest_verdict(
        strategy_id=sid,
        n_fills=n_fills,
        n_orders=n_orders,
        n_bars=n_used,
        data_source=src,
    )
    summary: dict[str, Any] = {
        "ok": True,
        "kind": "backtest",
        "strategy_id": sid,
        "params": strategy_params,
        "n_bars": n_used,
        "data_source": src,
        "instrument_id": iid,
        "n_fills": n_fills,
        "n_orders": n_orders,
        "accounting_ok": result.accounting.ok,
        "initial_equity": str(initial_cash),
        "final_equity": str(final_eq),
        "pnl": str(final_eq - initial_cash),
        "total_fees": str(total_fees),
        "avg_fee_per_fill": str(avg_fee_per_fill) if avg_fee_per_fill is not None else None,
        "fee_per_side": {
            "maker_bps": fee_dict.get("maker_bps"),
            "taker_bps": fee_dict.get("taker_bps"),
            "maker_pct": fee_dict.get("maker_pct"),
            "taker_pct": fee_dict.get("taker_pct"),
            "note": fee_dict.get("note", ""),
            "as_of": fee_dict.get("as_of", ""),
            "source_url": fee_dict.get("source_url", ""),
        },
        "fee_schedule": fee_dict,
        "fee_model": getattr(fee_model, "model_id", "fee.binance_spot_vip0.v1"),
        "bar_range": bar_range,
        "fills": detail["fills"],
        "orders": detail["orders"],
        "fills_truncated": detail["fills_truncated"],
        "orders_truncated": detail["orders_truncated"],
        "equity_curve_tail": detail["equity_curve_tail"],
        "verdict": verdict,
        "verdict_es": verdict_es,
        "metrics": dict(result.metrics.metrics),
        "metrics_version": result.metrics.metrics_version,
        "experiment_id": result.metrics.experiment_id,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }
    if reports_dir is not None:
        from quantlab.workbench.reports import persist_backtest_report

        persisted = persist_backtest_report(
            reports_dir,
            metrics=result.metrics,
            simulation=result.simulation,
            summary=summary,
        )
        summary["report_id"] = persisted["report_id"]
        summary["report_path"] = persisted["path"]
        summary["report_has_html"] = persisted["has_html"]
    converted = to_jsonable(summary)
    if not isinstance(converted, dict):
        raise ValidationError("serialización backtest inválida")
    return converted


def run_market_lab_backtest(
    *,
    strategy_id: str = "momentum",
    params: dict[str, Any] | None = None,
    venue: str,
    underlying: str,
    market_type: str = "futures",
    interval: str = "1h",
    period_days: int | float | str | None = None,
    n_bars: int | None = None,
    experiment_id: str = "wb-lab-backtest",
    reports_dir: Path | None = None,
    initial_cash: Decimal | None = None,
) -> dict[str, Any]:
    """Backtest sobre velas históricas públicas (misma MD que Sim / MC ligado).

    Exige ``venue`` + ``underlying``. Resuelve N velas desde ``period_days``
    (prioridad) o ``n_bars``. Fees = schedule VIP0 del mercado.
    """
    from quantlab.brokers.md_router import fetch_bars_for_instrument
    from quantlab.research.sim.fee_schedules import (
        fee_model_from_schedule,
        get_fee_schedule,
        schedule_to_lab_fee_dict,
    )
    from quantlab.research.sim.period_bars import estimate_n_bars

    v = str(venue or "").strip().lower()
    coin = str(underlying or "").strip().upper()
    if not v or not coin:
        raise ValidationError("backtest histórico: venue y moneda (underlying) requeridos")
    mt = str(market_type or "futures").strip().lower()
    if mt not in ("spot", "futures"):
        raise ValidationError("market_type debe ser spot o futures")
    iv = str(interval or "1h").strip()

    period_meta: dict[str, Any] | None = None
    if period_days is not None and str(period_days).strip() != "":
        period_meta = estimate_n_bars(period_days=period_days, interval=iv)
        kline_limit = int(period_meta["n_bars"])
    elif n_bars is not None:
        kline_limit = int(n_bars)
    else:
        period_meta = estimate_n_bars(period_days=30, interval=iv)
        kline_limit = int(period_meta["n_bars"])

    kline_limit = max(LAB_KLINE_LIMIT_MIN, min(kline_limit, LAB_KLINE_LIMIT_MAX))

    resolved, bars = fetch_bars_for_instrument(
        coin,
        venue=v,
        market_type=mt,
        interval=iv,
        kline_limit=kline_limit,
    )
    if len(bars) < 4:
        raise ValidationError(
            f"insuficientes velas para {v}/{coin} ({len(bars)}); "
            "probá otro período/TF o mercado"
        )
    run_bars = bars[-kline_limit:] if len(bars) > kline_limit else list(bars)

    fee_sched = get_fee_schedule(v, mt)
    fee_model = fee_model_from_schedule(fee_sched)
    fee_dict = schedule_to_lab_fee_dict(fee_sched)

    cash = initial_cash if initial_cash is not None else Decimal("10000")
    out = run_lab_backtest(
        strategy_id=strategy_id,
        params=params,
        bars=run_bars,
        instrument_id=resolved.instrument_id,
        data_source=f"{v}_{mt}_klines",
        experiment_id=experiment_id,
        reports_dir=reports_dir,
        initial_cash=cash,
        fee_model=fee_model,
        fee_schedule_meta=fee_dict,
    )
    # Contexto explícito para UI / memo (no cosmético: viene del fetch real).
    out["mode"] = "historical"
    out["venue"] = v
    out["underlying"] = resolved.underlying
    out["market_type"] = mt
    out["interval"] = iv
    out["period_days"] = (
        period_meta.get("period_days") if period_meta else None
    )
    out["requested_n_bars"] = kline_limit
    out["symbol"] = getattr(resolved, "symbol", None) or coin
    out["context"] = {
        "mode": "historical",
        "venue": v,
        "underlying": resolved.underlying,
        "market_type": mt,
        "interval": iv,
        "period_days": out.get("period_days"),
        "n_bars": out.get("n_bars"),
        "data_source": out.get("data_source"),
        "instrument_id": out.get("instrument_id"),
        "symbol": out.get("symbol"),
        "strategy_id": out.get("strategy_id"),
        "bar_range": out.get("bar_range"),
    }
    if kline_limit >= LAB_KLINE_HEAVY_WARN:
        out.setdefault("warnings", []).append(
            f"Horizonte pesado (~{kline_limit} velas): puede tardar."
        )
    return out


def run_lab_scanner(*, top_n: int = 3) -> dict[str, Any]:
    _validate_top_n(top_n)
    universe = make_scanner_universe()
    result = AlphaScanner().scan(universe, top_n=top_n, min_bars=3)
    return {
        "ok": True,
        "kind": "scanner",
        "top_n": top_n,
        "selected": list(result.selected),
        "scores": [dataclass_to_dict(s) for s in result.scores],
        "gap_events": list(result.gap_events),
        "schema_version": result.schema_version,
        "live_routing": False,
    }


def _apply_kronos_enrichment(
    out: dict[str, Any],
    bars_by_instrument: Mapping[str, Sequence[Bar]],
    *,
    profile: str,
    interval: str,
    kronos: Mapping[str, Any] | None = None,
    persist_dir: Path | None = None,
) -> dict[str, Any]:
    """Kronos-inside-Scanner: re-rankea con forecast del tramo de ranking."""
    from dataclasses import replace

    from quantlab.research.alpha.kronos import apply_kronos_to_scan, kronos_config_from_mapping

    cfg = kronos_config_from_mapping(dict(kronos) if kronos else None)
    # Timeout por símbolo escalado (CPU notebook: ~0.5–1.5 s por muestra).
    per_symbol = max(30.0, float(cfg.sample_count) * 8.0)
    if cfg.timeout_seconds < per_symbol:
        cfg = replace(cfg, timeout_seconds=per_symbol)
    # Cap pred_len al contexto del modelo.
    pred = cfg.resolved_pred_len(interval)
    if pred > cfg.max_context // 2:
        cfg = replace(cfg, pred_len=min(pred, cfg.max_context // 2))
    # Moneda puntual / pocas filas: no tiene sentido Top Kronos 20/30.
    scores = out.get("scores")
    n_scores = len(scores) if isinstance(scores, list) else 0
    requested = out.get("requested_underlyings")
    if isinstance(requested, list) and requested:
        n_cap = max(1, len(requested))
    elif n_scores > 0:
        n_cap = n_scores
    else:
        n_cap = cfg.resolved_top_n()
    if cfg.resolved_top_n() > n_cap:
        cfg = replace(cfg, top_n=n_cap)
    cache_dir = (persist_dir / "kronos_cache") if persist_dir is not None else None
    return apply_kronos_to_scan(
        out,
        bars_by_instrument,
        config=cfg,
        profile=profile,
        interval=interval,
        cache_dir=cache_dir,
    )


def run_binance_lab_scanner(
    *,
    top_n: int = 5,
    symbol_limit: int = 15,
    interval: str = "1h",
    kline_limit: int = 24,
    base_url: str | None = None,
    profile: str = "legacy_v1",
    persist_dir: Path | None = None,
    kronos: Mapping[str, Any] | None = None,
    include_ml: bool = True,
) -> dict[str, Any]:
    """AlphaScanner / perfiles sobre klines Binance públicas (read-only)."""
    from quantlab.brokers.binance.public_md import (
        DEFAULT_BASE_URL,
        BinancePublicMdClient,
        fetch_universe_bars,
        validate_kline_interval,
    )

    _validate_top_n(top_n)
    _validate_symbol_limit(symbol_limit)
    if kline_limit < LAB_KLINE_LIMIT_MIN or kline_limit > LAB_KLINE_LIMIT_MAX:
        raise ValidationError(
            f"kline_limit debe estar entre {LAB_KLINE_LIMIT_MIN} y {LAB_KLINE_LIMIT_MAX}"
        )
    interval = validate_kline_interval(interval)
    from quantlab.research.alpha.recommend import resolve_scoring_profile

    requested_profile, profile_key, _auto = resolve_scoring_profile(profile)

    url = base_url or DEFAULT_BASE_URL
    client = BinancePublicMdClient(base_url=url)
    fetch_cap = _fetch_cap_for_limit(symbol_limit, venue="binance", market_type="spot")
    symbols = client.list_spot_symbols(quote="USDT", limit=fetch_cap)
    if not symbols:
        raise ValidationError("sin símbolos USDT de Binance")

    bars_by_symbol = fetch_universe_bars(
        symbols,
        interval=interval,
        kline_limit=kline_limit,
        base_url=url,
    )
    from quantlab.research.alpha.quality import EligibilityConfig
    from quantlab.research.alpha.universe import (
        build_universe_from_symbol_bars,
        exclusion_reason_counts,
    )

    fetch_failures = {
        s: "klines omitidas o inválidas" for s in symbols if s not in bars_by_symbol
    }
    built = build_universe_from_symbol_bars(
        venue="binance",
        symbols=symbols,
        bars_by_symbol=bars_by_symbol,
        network="mainnet",
        market_type="spot",
        instrument_prefix="BN:",
        eligibility_config=EligibilityConfig(min_bars=3, min_completeness=0.5),
        fetch_failures=fetch_failures,
    )
    universe = built.eligible_bars
    if not universe:
        raise ValidationError(
            "ningún símbolo elegible tras filtros de calidad "
            f"(fetched={len(bars_by_symbol)}, excluded={len(built.exclusions)})"
        )

    symbol_map = {
        inst.normalized_instrument: inst.original_symbol for inst in built.instruments
    }

    scores_out: list[dict[str, Any]]
    selected: list[str]
    gap_events: list[str] = []
    schema_version = "1.0"
    persisted: dict[str, Any] | None = None

    if profile_key in ("legacy_v1", "legacy"):
        result = AlphaScanner().scan(universe, top_n=top_n, min_bars=3)
        selected = list(result.selected)
        scores_out = [dataclass_to_dict(s) for s in result.scores]
        gap_events = list(result.gap_events)
        schema_version = result.schema_version
        profile_key = "legacy_v1"
    else:
        from quantlab.research.alpha.profiles import build_profile, score_with_profile

        try:
            build_profile(profile_key)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rows = score_with_profile(universe, profile_key)
        ranked = [r for r in rows if not r.excluded]
        selected = [r.instrument_id for r in ranked[: max(0, top_n)]]
        scores_out = []
        for r in ranked:
            raw_by = {c.name: c.raw for c in r.components}
            scores_out.append(
                {
                    "instrument_id": r.instrument_id,
                    "volatility": raw_by.get("volatility"),
                    "volume_score": raw_by.get("volume"),
                    "liquidity_score": raw_by.get("liquidity"),
                    "composite": r.composite,
                    "base_score": r.base_score,
                    "components": [
                        {
                            "name": c.name,
                            "raw": c.raw,
                            "normalized": c.normalized,
                            "weight": c.weight,
                            "contribution": c.contribution,
                            "available": c.available,
                        }
                        for c in r.components
                    ],
                    "penalties": [
                        {"name": p.name, "value": p.value, "detail": p.detail} for p in r.penalties
                    ],
                }
            )
        if persist_dir is not None:
            from quantlab.research.alpha.persist import ScanStore, hash_bars_fingerprint

            meta = ScanStore(persist_dir).save_scored(
                profile=profile_key,
                rows=rows,
                bars_hash=hash_bars_fingerprint(universe),
                request={
                    "profile": profile_key,
                    "top_n": top_n,
                    "interval": interval,
                    "kline_limit": kline_limit,
                    "symbol_limit": symbol_limit,
                },
            )
            persisted = meta.to_dict()

    selected_symbols = [symbol_map.get(iid, iid) for iid in selected]

    out: dict[str, Any] = {
        "ok": True,
        "kind": "binance_scanner",
        "venue": "binance",
        "market_type": "spot",
        "top_n": top_n,
        "symbol_limit": symbol_limit,
        "universe_mode": "all" if symbol_limit == SYMBOL_LIMIT_ALL else "batch",
        "n_universe": len(symbols),
        "interval": interval,
        "kline_limit": kline_limit,
        "n_symbols_fetched": len(bars_by_symbol),
        "fetched": len(symbols),
        "eligible": len(universe),
        "excluded": len(built.exclusions),
        "exclusion_counts": exclusion_reason_counts(built.exclusions),
        "exclusions": [e.to_dict() for e in built.exclusions],
        "selected": selected,
        "selected_symbols": selected_symbols,
        "scores": scores_out,
        "gap_events": gap_events,
        "schema_version": schema_version,
        "scanner_version": "alpha-v2-contracts",
        "profile": profile_key,
        "read_only": True,
        "live_routing": False,
        "note": (
            "Un score alto indica adecuación al perfil seleccionado, "
            "no rentabilidad garantizada."
            + (
                f" Universo completo pedido: {len(symbols)} USDT TRADING."
                if symbol_limit == SYMBOL_LIMIT_ALL
                else ""
            )
        ),
    }
    if persisted is not None:
        out["persisted"] = persisted
    from quantlab.research.alpha.recommend import attach_recommendations
    from quantlab.research.alpha.scan_quality import attach_scan_quality

    # underlying + familia/estrategias/TF para UI (Guided Lab + Alpha Scanner)
    for row in out["scores"]:
        if isinstance(row, dict) and "underlying" not in row:
            iid = str(row.get("instrument_id") or "")
            sym = symbol_map.get(iid, iid.split(":", 1)[-1] if ":" in iid else iid)
            row["symbol"] = sym
            from quantlab.research.alpha.recommend import underlying_from_symbol

            row["underlying"] = underlying_from_symbol(sym)
    out["profile"] = requested_profile
    attach_scan_quality(out, fetch_failures=fetch_failures)
    scoring_profile = profile_key if profile_key else requested_profile
    out = _apply_kronos_enrichment(
        out,
        universe,
        profile=scoring_profile,
        interval=interval,
        kronos=kronos,
        persist_dir=persist_dir,
    )
    out = attach_recommendations(out, profile=requested_profile, interval=interval)
    from quantlab.research.alpha.individual_export import attach_individual_signals
    from quantlab.research.alpha.ml.attach import attach_ml_ranking_signals

    out = attach_individual_signals(out)
    exp = persist_dir.parent if persist_dir is not None else None
    return attach_ml_ranking_signals(out, experiments_dir=exp, enabled=include_ml)


_VENUE_SCAN_PREFIX: dict[str, dict[str, str]] = {
    "binance": {"spot": "BN:", "futures": "BNF:"},
    "okx": {"spot": "OKX:", "futures": "OKX:"},
    "bybit": {"spot": "BYB:", "futures": "BYB:"},
    "hyperliquid": {"spot": "HL:", "futures": "HL:"},
    "a3": {"spot": "A3:", "futures": "A3:"},
}

# Universo: cantidad libre (1..MAX) o 0 = todas las disponibles del venue.
SCANNER_SYMBOL_BATCHES: tuple[int, ...] = (20, 30, 40, 50)  # presets UI (hints)
SYMBOL_LIMIT_ALL = 0
SYMBOL_LIMIT_MIN = 1
SYMBOL_LIMIT_MAX = 500
# Ranking «Top» y Top Kronos: cantidad libre.
SCANNER_TOP_N_MIN = 1
SCANNER_TOP_N_MAX = 100
# Tope práctico al pedir «todas» en Binance spot (USDT TRADING).
SYMBOL_LIMIT_ALL_BINANCE_SPOT = 2000
# Anclas para min-max cuando el usuario pide 1–2 monedas (puntual).
SCORE_ANCHOR_UNDERLYINGS: tuple[str, ...] = ("BTC", "ETH", "SOL")
SCORE_CROSS_SECTION_MIN = 3


def _validate_top_n(top_n: int) -> None:
    if top_n < SCANNER_TOP_N_MIN or top_n > SCANNER_TOP_N_MAX:
        raise ValidationError(
            f"top_n debe estar entre {SCANNER_TOP_N_MIN} y {SCANNER_TOP_N_MAX}"
        )


def _validate_symbol_limit(symbol_limit: int) -> None:
    if symbol_limit == SYMBOL_LIMIT_ALL:
        return
    if symbol_limit < SYMBOL_LIMIT_MIN or symbol_limit > SYMBOL_LIMIT_MAX:
        raise ValidationError(
            f"symbol_limit debe ser {SYMBOL_LIMIT_ALL} (todas) o entre "
            f"{SYMBOL_LIMIT_MIN} y {SYMBOL_LIMIT_MAX}"
        )


def _fetch_cap_for_limit(symbol_limit: int, *, venue: str, market_type: str) -> int:
    """Convierte tanda/«todas» al tope de fetch (no es el tamaño real del mercado)."""
    if symbol_limit != SYMBOL_LIMIT_ALL:
        return symbol_limit
    v = venue.strip().lower()
    mt = market_type.strip().lower()
    if v == "binance" and mt in ("spot", "futures"):
        return SYMBOL_LIMIT_ALL_BINANCE_SPOT
    # Curados (SIM_COINS / A3): pedir de más; el slice usa len(lista).
    return 10_000

def run_venue_lab_scanner(
    *,
    venue: str = "binance",
    market_type: str = "spot",
    top_n: int = 5,
    symbol_limit: int = 20,
    interval: str = "1h",
    kline_limit: int | None = 24,
    period_days: int | float | str | None = None,
    profile: str = "legacy_v1",
    underlyings: Sequence[str] | None = None,
    persist_dir: Path | None = None,
    kronos: Mapping[str, Any] | None = None,
    include_ml: bool = True,
) -> dict[str, Any]:
    """Alpha ranking sobre MD público real (Binance/OKX/Bybit/HL).

    Binance spot sin ``underlyings``: lista USDT del exchange (mismo path F111).
    Resto: universo curado SIM_COINS (o lista explícita) vía ``md_router``.

    Si viene ``period_days``, se convierte a N velas (prioridad sobre kline_limit
    solo cuando kline_limit es None). Si ambos vienen, gana ``kline_limit``.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from quantlab.brokers.md_router import fetch_bars_for_instrument
    from quantlab.research.alpha.quality import EligibilityConfig
    from quantlab.research.alpha.recommend import (
        attach_recommendations,
        resolve_scoring_profile,
        underlying_from_symbol,
    )
    from quantlab.research.alpha.universe import (
        build_universe_from_symbol_bars,
        exclusion_reason_counts,
    )
    from quantlab.research.sim.period_bars import estimate_n_bars
    from quantlab.research.sim.universe import SIM_COINS

    v = (venue or "binance").strip().lower()
    mt = (market_type or "spot").strip().lower()
    if v not in _VENUE_SCAN_PREFIX:
        raise ValidationError(
            f"venue no soportado para scanner: {venue!r}; "
            f"permitidos: {', '.join(sorted(_VENUE_SCAN_PREFIX))}"
        )
    if mt not in ("spot", "futures"):
        raise ValidationError("market_type debe ser spot o futures")
    if v == "hyperliquid" and mt == "spot":
        raise ValidationError("hyperliquid en lab: usar market_type=futures (perps)")
    if v == "a3" and mt == "spot":
        raise ValidationError("a3 en lab: usar market_type=futures (contratos con vencimiento)")
    _validate_top_n(top_n)
    _validate_symbol_limit(symbol_limit)

    requested_profile, profile_key, _auto = resolve_scoring_profile(profile)

    resolved_limit: int
    period_meta: dict[str, Any] | None = None
    if kline_limit is not None:
        resolved_limit = int(kline_limit)
    elif period_days is not None:
        period_meta = estimate_n_bars(period_days=period_days, interval=interval)
        resolved_limit = min(int(period_meta["n_bars"]), LAB_KLINE_LIMIT_MAX)
        resolved_limit = max(resolved_limit, LAB_KLINE_LIMIT_MIN)
    else:
        resolved_limit = 24

    if resolved_limit < LAB_KLINE_LIMIT_MIN or resolved_limit > LAB_KLINE_LIMIT_MAX:
        raise ValidationError(
            f"kline_limit debe estar entre {LAB_KLINE_LIMIT_MIN} y {LAB_KLINE_LIMIT_MAX} "
            f"(recibido {resolved_limit})"
        )
    kline_limit = resolved_limit

    # Path Binance spot listado exchange (volumen real de mercado)
    if v == "binance" and mt == "spot" and underlyings is None:
        out_bn = run_binance_lab_scanner(
            top_n=top_n,
            symbol_limit=symbol_limit,
            interval=interval,
            kline_limit=kline_limit,
            profile=profile,
            persist_dir=persist_dir,
            kronos=kronos,
            include_ml=include_ml,
        )
        out_bn["market_type"] = "spot"
        if period_meta is not None:
            out_bn["period_days"] = period_meta.get("period_days")
            out_bn["n_bars_estimate"] = period_meta.get("n_bars")
        return out_bn

    requested_underlyings: list[str] | None = None
    score_anchors: list[str] = []
    if underlyings is not None:
        coins = [str(u).strip() for u in underlyings if str(u).strip()]
        if not coins:
            raise ValidationError("underlyings vacío: escribí al menos una moneda")
        # Dedup preservando orden (case-insensitive).
        seen_u: set[str] = set()
        requested_underlyings = []
        for c in coins:
            key = c.upper()
            if key in seen_u:
                continue
            seen_u.add(key)
            requested_underlyings.append(key)
        coins = list(requested_underlyings)
    elif v == "a3":
        from quantlab.research.sim.universe import A3_CURATED_PRODUCTS

        coins = [str(c["id"]) for c in A3_CURATED_PRODUCTS]
        if len(coins) < 3:
            raise ValidationError("se requieren al menos 3 underlyings para el scan")
    else:
        coins = [str(c["id"]) for c in SIM_COINS]
        if len(coins) < 3:
            raise ValidationError("se requieren al menos 3 underlyings para el scan")
    if symbol_limit != SYMBOL_LIMIT_ALL:
        coins = coins[:symbol_limit]

    # Moneda puntual / pocas: anclar cross-section con majors (no se listan al final).
    if (
        requested_underlyings is not None
        and len(requested_underlyings) < SCORE_CROSS_SECTION_MIN
    ):
        have = {c.upper() for c in coins}
        for anchor in SCORE_ANCHOR_UNDERLYINGS:
            if len(coins) >= SCORE_CROSS_SECTION_MIN:
                break
            if anchor in have:
                continue
            coins.append(anchor)
            score_anchors.append(anchor)
            have.add(anchor)

    bars_by_symbol: dict[str, list[Bar]] = {}
    symbol_to_underlying: dict[str, str] = {}
    fetch_failures: dict[str, str] = {}
    symbols: list[str] = []

    def _one(u: str) -> tuple[str, str, list[Bar] | None, str | None]:
        try:
            resolved, bars = fetch_bars_for_instrument(
                u,
                venue=v,
                market_type=mt,
                interval=interval,
                kline_limit=kline_limit,
            )
            return resolved.symbol, resolved.underlying, list(bars), None
        except Exception as exc:  # noqa: BLE001 — fail-soft por símbolo
            return u, u, None, str(exc)

    workers = min(8, max(1, len(coins)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_one, u): u for u in coins}
        for fut in as_completed(futs):
            sym, und, bars, err = fut.result()
            if err or not bars:
                fetch_failures[sym] = err or "sin barras"
                continue
            bars_by_symbol[sym] = bars
            symbol_to_underlying[sym] = und
            symbols.append(sym)

    if not symbols:
        # Moneda puntual: mensaje claro si lo pedido no tiene MD (aunque fallen anclas).
        if requested_underlyings is not None:
            detail = "; ".join(
                f"{u}: {fetch_failures.get(u) or 'sin MD'}" for u in requested_underlyings
            )
            raise ValidationError(
                f"no se encontró {v}/{mt} para "
                f"{', '.join(requested_underlyings)} ({detail}). "
                "Revisá el ticker (ej. HOT = Holo en Binance spot HOTUSDT) "
                "o probá otro venue/mercado."
            )
        raise ValidationError(
            f"sin klines en {v}/{mt} "
            f"(fallos={len(fetch_failures)}; ej. {next(iter(fetch_failures.values()), '—')})"
        )

    if requested_underlyings is not None:
        got_und = {
            str(symbol_to_underlying.get(s) or underlying_from_symbol(s)).strip().upper()
            for s in symbols
        }
        missing_req = [u for u in requested_underlyings if u not in got_und]
        # 1 moneda o todas fallaron: error explícito (no listar solo anclas).
        if missing_req and (
            len(requested_underlyings) == 1 or len(missing_req) == len(requested_underlyings)
        ):
            detail = "; ".join(
                f"{u}: {fetch_failures.get(u) or 'sin MD / no elegible'}" for u in missing_req
            )
            raise ValidationError(
                f"no se encontró {v}/{mt} para "
                f"{', '.join(missing_req)} ({detail}). "
                "Revisá el ticker (ej. HOT = Holo en Binance spot HOTUSDT) "
                "o probá otro venue/mercado."
            )

    prefix = _VENUE_SCAN_PREFIX[v][mt]
    built = build_universe_from_symbol_bars(
        venue=v,
        symbols=symbols,
        bars_by_symbol=bars_by_symbol,
        network="mainnet",
        market_type=mt,
        instrument_prefix=prefix,
        eligibility_config=EligibilityConfig(min_bars=3, min_completeness=0.5),
        fetch_failures=fetch_failures,
    )
    universe = built.eligible_bars
    if not universe:
        raise ValidationError(
            "ningún símbolo elegible tras filtros de calidad "
            f"(fetched={len(bars_by_symbol)}, excluded={len(built.exclusions)})"
        )

    symbol_map = {
        inst.normalized_instrument: inst.original_symbol for inst in built.instruments
    }

    scores_out: list[dict[str, Any]]
    selected: list[str]
    gap_events: list[str] = []
    schema_version = "1.0"
    persisted: dict[str, Any] | None = None

    if profile_key in ("legacy_v1", "legacy"):
        result = AlphaScanner().scan(universe, top_n=top_n, min_bars=3)
        selected = list(result.selected)
        scores_out = [dataclass_to_dict(s) for s in result.scores]
        gap_events = list(result.gap_events)
        schema_version = result.schema_version
        profile_key = "legacy_v1"
    else:
        from quantlab.research.alpha.profiles import build_profile, score_with_profile

        try:
            build_profile(profile_key)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rows = score_with_profile(universe, profile_key)
        ranked = [r for r in rows if not r.excluded]
        selected = [r.instrument_id for r in ranked[: max(0, top_n)]]
        scores_out = []
        for r in ranked:
            raw_by = {c.name: c.raw for c in r.components}
            scores_out.append(
                {
                    "instrument_id": r.instrument_id,
                    "volatility": raw_by.get("volatility"),
                    "volume_score": raw_by.get("volume"),
                    "liquidity_score": raw_by.get("liquidity"),
                    "composite": r.composite,
                    "base_score": r.base_score,
                    "components": [
                        {
                            "name": c.name,
                            "raw": c.raw,
                            "normalized": c.normalized,
                            "weight": c.weight,
                            "contribution": c.contribution,
                            "available": c.available,
                        }
                        for c in r.components
                    ],
                    "penalties": [
                        {"name": p.name, "value": p.value, "detail": p.detail} for p in r.penalties
                    ],
                }
            )
        if persist_dir is not None:
            from quantlab.research.alpha.persist import ScanStore, hash_bars_fingerprint

            meta = ScanStore(persist_dir).save_scored(
                profile=profile_key,
                rows=rows,
                bars_hash=hash_bars_fingerprint(universe),
                request={
                    "profile": profile_key,
                    "top_n": top_n,
                    "interval": interval,
                    "kline_limit": kline_limit,
                    "symbol_limit": symbol_limit,
                    "venue": v,
                    "market_type": mt,
                    "period_days": period_days,
                },
            )
            persisted = meta.to_dict()

    selected_symbols = [symbol_map.get(iid, iid) for iid in selected]
    for row in scores_out:
        if not isinstance(row, dict):
            continue
        iid = str(row.get("instrument_id") or "")
        sym = symbol_map.get(iid, iid.split(":", 1)[-1] if ":" in iid else iid)
        row["symbol"] = sym
        row["underlying"] = symbol_to_underlying.get(sym) or underlying_from_symbol(sym)

    if requested_underlyings is not None:
        # Siempre filtrar a lo pedido (anclas solo sirven para cross-section).
        want = {u.upper() for u in requested_underlyings}
        scores_out = [
            r
            for r in scores_out
            if isinstance(r, dict)
            and str(r.get("underlying") or "").strip().upper() in want
        ]
        selected = [
            iid
            for iid in selected
            if str(
                symbol_to_underlying.get(symbol_map.get(iid, iid), "")
                or underlying_from_symbol(symbol_map.get(iid, iid))
            )
            .strip()
            .upper()
            in want
        ]
        selected_symbols = [symbol_map.get(iid, iid) for iid in selected]
        if not scores_out:
            raise ValidationError(
                "moneda puntual sin score tras filtros: "
                + ", ".join(requested_underlyings)
                + (
                    f" (fallos MD: {fetch_failures})"
                    if fetch_failures
                    else " (excluida por calidad o no elegible)"
                )
            )

    if requested_underlyings is not None:
        universe_mode = (
            "puntual"
            if len(requested_underlyings) < SCORE_CROSS_SECTION_MIN
            else "custom"
        )
    elif symbol_limit == SYMBOL_LIMIT_ALL:
        universe_mode = "all"
    else:
        universe_mode = "batch"

    out: dict[str, Any] = {
        "ok": True,
        "kind": "venue_scanner",
        "venue": v,
        "market_type": mt,
        "top_n": top_n,
        "symbol_limit": symbol_limit,
        "universe_mode": universe_mode,
        "n_universe": len(coins),
        "interval": interval,
        "kline_limit": kline_limit,
        "n_symbols_fetched": len(bars_by_symbol),
        "fetched": len(symbols),
        "eligible": len(universe),
        "excluded": len(built.exclusions),
        "exclusion_counts": exclusion_reason_counts(built.exclusions),
        "exclusions": [e.to_dict() for e in built.exclusions],
        "selected": selected,
        "selected_symbols": selected_symbols,
        "selected_underlyings": [
            symbol_to_underlying.get(s) or underlying_from_symbol(s) for s in selected_symbols
        ],
        "scores": scores_out,
        "gap_events": gap_events,
        "schema_version": schema_version,
        "scanner_version": "alpha-v2-venue-md",
        "profile": profile_key,
        "read_only": True,
        "live_routing": False,
        "note": (
            "MD público real (read-only). Un score alto indica adecuación al perfil, "
            "no rentabilidad garantizada."
            + (
                f" Universo completo del venue: {len(coins)} activos pedidos."
                if symbol_limit == SYMBOL_LIMIT_ALL and not score_anchors
                else ""
            )
            + (
                " Moneda puntual: score relativo a anclas "
                + "/".join(score_anchors)
                + " (no listadas)."
                if score_anchors
                else ""
            )
        ),
    }
    if requested_underlyings is not None:
        out["requested_underlyings"] = list(requested_underlyings)
    if score_anchors:
        out["score_mode"] = "anchored_cross_section"
        out["score_anchors"] = list(score_anchors)
    if period_meta is not None:
        out["period_days"] = period_meta.get("period_days")
        out["n_bars_estimate"] = period_meta.get("n_bars")
    if persisted is not None:
        out["persisted"] = persisted
    if fetch_failures:
        out["fetch_failures"] = dict(fetch_failures)
    out["profile"] = requested_profile
    md_meta: dict[str, Any] | None = None
    if v == "a3":
        from quantlab.brokers.a3.md_backend import try_build_env_md_backend

        env_b, md_reason = try_build_env_md_backend()
        md_meta = (
            {"provider": "a3-env", "source": "pyrofex"}
            if env_b is not None
            else {
                "provider": "a3-fake",
                "source": "fake",
                "fallback_reason": md_reason,
            }
        )
        out["md_meta"] = md_meta
    from quantlab.research.alpha.scan_quality import attach_scan_quality

    attach_scan_quality(out, fetch_failures=fetch_failures, md_meta=md_meta)
    scoring_profile = profile_key if profile_key else requested_profile
    out = _apply_kronos_enrichment(
        out,
        universe,
        profile=scoring_profile,
        interval=interval,
        kronos=kronos,
        persist_dir=persist_dir,
    )
    out = attach_recommendations(out, profile=requested_profile, interval=interval)
    from quantlab.research.alpha.individual_export import attach_individual_signals
    from quantlab.research.alpha.ml.attach import attach_ml_ranking_signals

    out = attach_individual_signals(out)
    exp = persist_dir.parent if persist_dir is not None else None
    return attach_ml_ranking_signals(out, experiments_dir=exp, enabled=include_ml)


def _composite_of_score_row(row: Mapping[str, Any]) -> float:
    try:
        if row.get("composite") is not None:
            return float(row["composite"])
        if row.get("base_score") is not None:
            return float(row["base_score"])
    except (TypeError, ValueError):
        return 0.0
    return 0.0


def build_cross_venue_comparison(
    by_venue: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compara scores de la misma moneda entre venues (pts = composite×100)."""
    # underlying -> list of {venue, market_type, composite, rank}
    by_und: dict[str, list[dict[str, Any]]] = {}
    venue_summary: list[dict[str, Any]] = []

    for block in by_venue:
        venue = str(block.get("venue") or "")
        mt = str(block.get("market_type") or "")
        scores = block.get("scores")
        if not isinstance(scores, list) or not scores:
            venue_summary.append(
                {
                    "venue": venue,
                    "market_type": mt,
                    "top_composite": None,
                    "top_underlying": None,
                    "n_scores": 0,
                    "mean_top": None,
                }
            )
            continue
        comps: list[float] = []
        for i, row in enumerate(scores):
            if not isinstance(row, Mapping):
                continue
            und = str(row.get("underlying") or row.get("symbol") or "").strip().upper()
            if not und:
                continue
            c = _composite_of_score_row(row)
            comps.append(c)
            by_und.setdefault(und, []).append(
                {
                    "venue": venue,
                    "market_type": mt,
                    "composite": round(c, 6),
                    "pts": round(c * 100.0, 2),
                    "rank": i + 1,
                }
            )
        top_row = scores[0] if isinstance(scores[0], Mapping) else {}
        top_c = _composite_of_score_row(top_row) if top_row else None
        mean_top = (sum(comps[:5]) / len(comps[:5])) if comps else None
        venue_summary.append(
            {
                "venue": venue,
                "market_type": mt,
                "top_composite": round(top_c, 6) if top_c is not None else None,
                "top_pts": round(top_c * 100.0, 2) if top_c is not None else None,
                "top_underlying": str(
                    top_row.get("underlying") or top_row.get("symbol") or ""
                ),
                "n_scores": len(comps),
                "mean_top": round(mean_top, 6) if mean_top is not None else None,
                "mean_top_pts": round(mean_top * 100.0, 2) if mean_top is not None else None,
            }
        )

    comparisons: list[dict[str, Any]] = []
    for und, rows in sorted(by_und.items()):
        if len(rows) < 2:
            continue
        ordered = sorted(rows, key=lambda r: (-float(r["composite"]), r["venue"]))
        best = ordered[0]
        second = ordered[1]
        delta_pts = round(float(best["pts"]) - float(second["pts"]), 2)
        comparisons.append(
            {
                "underlying": und,
                "rows": ordered,
                "best_venue": best["venue"],
                "best_composite": best["composite"],
                "best_pts": best["pts"],
                "delta_pts": delta_pts,
                "text": (
                    f"{und}: mejor en {best['venue']} "
                    f"({best['pts']:.1f} pts) · "
                    f"+{delta_pts:.1f} pts vs {second['venue']}"
                    if delta_pts > 0
                    else f"{und}: empate / casi igual entre {best['venue']} y {second['venue']}"
                ),
            }
        )
    comparisons.sort(key=lambda x: (-float(x["delta_pts"]), x["underlying"]))

    # Mejor venue por media del top
    best_venue_block = None
    for vs in venue_summary:
        if vs.get("mean_top") is None:
            continue
        if best_venue_block is None or float(vs["mean_top"]) > float(
            best_venue_block["mean_top"]
        ):
            best_venue_block = vs

    headline = ""
    if best_venue_block and len([v for v in venue_summary if v.get("mean_top") is not None]) >= 2:
        others = [
            v
            for v in venue_summary
            if v.get("venue") != best_venue_block["venue"] and v.get("mean_top") is not None
        ]
        if others:
            other = max(others, key=lambda v: float(v["mean_top"]))
            d = round(
                float(best_venue_block["mean_top_pts"]) - float(other["mean_top_pts"]),
                2,
            )
            headline = (
                f"Hoy, con esta rama, el top promedio rinde mejor en "
                f"{best_venue_block['venue']} "
                f"({best_venue_block['mean_top_pts']:.1f} pts) · "
                f"+{d:.1f} pts vs {other['venue']}."
            )

    return {
        "headline": headline,
        "venue_summary": venue_summary,
        "by_underlying": comparisons[:40],
        "note": (
            "pts = score×100 (0–100). Delta = ventaja del mejor venue vs el segundo "
            "para la misma moneda. No es rentabilidad garantizada."
        ),
    }


def run_multi_venue_lab_scanner(
    *,
    venues: Sequence[str],
    market_type: str = "spot",
    top_n: int = 5,
    symbol_limit: int = 20,
    interval: str = "1h",
    kline_limit: int | None = 24,
    period_days: int | float | str | None = None,
    profile: str = "trend",
    underlyings: Sequence[str] | None = None,
    persist_dir: Path | None = None,
    kronos: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Corre el scanner en cada venue y devuelve resultados separados + comparación."""
    raw = [(v or "").strip().lower() for v in venues]
    ordered: list[str] = []
    for v in raw:
        if v and v not in ordered:
            ordered.append(v)
    if not ordered:
        raise ValidationError("venues vacío: marcá al menos un mercado")
    for v in ordered:
        if v not in _VENUE_SCAN_PREFIX:
            raise ValidationError(
                f"venue no soportado: {v!r}; "
                f"permitidos: {', '.join(sorted(_VENUE_SCAN_PREFIX))}"
            )

    mt_req = (market_type or "spot").strip().lower()
    by_venue: list[dict[str, Any]] = []
    venue_errors: list[dict[str, str]] = []

    for v in ordered:
        mt = mt_req
        note_extra = ""
        if v == "hyperliquid" and mt == "spot":
            mt = "futures"
            note_extra = "HL forzado a futures (perps)"
        if v == "a3" and mt == "spot":
            mt = "futures"
            note_extra = "A3 forzado a futures (vencimiento / granos)"
        try:
            block = run_venue_lab_scanner(
                venue=v,
                market_type=mt,
                top_n=top_n,
                symbol_limit=symbol_limit,
                interval=interval,
                kline_limit=kline_limit,
                period_days=period_days,
                profile=profile,
                underlyings=underlyings,
                persist_dir=persist_dir,
                kronos=kronos,
            )
            if note_extra:
                block = dict(block)
                block["note"] = (str(block.get("note") or "") + " · " + note_extra).strip(
                    " ·"
                )
            by_venue.append(block)
        except ValidationError as exc:
            venue_errors.append({"venue": v, "market_type": mt, "error": str(exc)})

    if not by_venue:
        raise ValidationError(
            "ningún venue devolvió scan: "
            + "; ".join(f"{e['venue']}={e['error']}" for e in venue_errors)
        )

    comparison = build_cross_venue_comparison(by_venue)
    primary = by_venue[0]
    from quantlab.research.alpha.recommend import (
        PROFILE_AUTO,
        SCORING_PROFILE_AUTO,
        build_auto_proposal,
        is_auto_profile,
    )

    out: dict[str, Any] = {
        "ok": True,
        "kind": "multi_venue_scanner",
        "venues": [b.get("venue") for b in by_venue],
        "venues_requested": ordered,
        "market_type": mt_req,
        "top_n": top_n,
        "symbol_limit": symbol_limit,
        "interval": interval,
        "kline_limit": primary.get("kline_limit"),
        "period_days": primary.get("period_days"),
        "profile": primary.get("profile") or profile,
        "by_venue": by_venue,
        "venue_errors": venue_errors,
        "comparison": comparison,
        "venue": primary.get("venue"),
        "scores": primary.get("scores"),
        "selected": primary.get("selected"),
        "selected_symbols": primary.get("selected_symbols"),
        "selected_underlyings": primary.get("selected_underlyings"),
        "recommendations": primary.get("recommendations"),
        "kronos": primary.get("kronos"),
        "read_only": True,
        "live_routing": False,
        "note": (
            "Scan separado por mercado. Usá la comparación (pts) para ver dónde "
            "la misma moneda / rama rinde mejor hoy. Score ≠ rentabilidad."
        ),
    }
    # Avisos agregados de cada venue (p.ej. A3 fake / scores empatados en 0)
    agg_warn: list[str] = []
    worst = "ok"
    for block in by_venue:
        for w in block.get("warnings") or []:
            if isinstance(w, str) and w not in agg_warn:
                agg_warn.append(w)
        st = str(block.get("score_status") or "ok")
        if st == "degraded":
            worst = "degraded"
        elif st == "partial" and worst == "ok":
            worst = "partial"
    if agg_warn:
        out["warnings"] = agg_warn
        out["score_status"] = worst
        out["score_reason"] = str(primary.get("score_reason") or worst)
    if is_auto_profile(profile) or is_auto_profile(str(primary.get("profile") or "")):
        merged_scores: list[Any] = []
        proposal_by_venue: list[dict[str, Any]] = []
        for block in by_venue:
            prop = block.get("proposal")
            if not isinstance(prop, dict):
                prop = build_auto_proposal(
                    block.get("scores") or [],
                    interval=str(block.get("interval") or interval or "1h"),
                    venue=str(block.get("venue") or ""),
                    top_n=top_n,
                )
            proposal_by_venue.append(
                {
                    "venue": block.get("venue"),
                    "market_type": block.get("market_type"),
                    "proposal": prop,
                }
            )
            scores = block.get("scores") or []
            if isinstance(scores, list):
                merged_scores.extend(scores[:top_n])
        out["auto_mode"] = True
        out["profile"] = PROFILE_AUTO
        out["scoring_profile"] = SCORING_PROFILE_AUTO
        out["proposal_by_venue"] = proposal_by_venue
        out["proposal"] = build_auto_proposal(
            merged_scores,
            interval=str(interval or primary.get("interval") or "1h"),
            venue=None,
            top_n=max(top_n, len(merged_scores) or top_n),
        )
        out["note"] = (
            "Modo Auto multi-venue: ranking equilibrado + propuesta global y por mercado. "
            "Score ≠ rentabilidad."
        )
    return out


def list_alpha_profiles() -> dict[str, Any]:
    """Catálogo Alpha Scanner = Auto + familias del Simulador (sin Demo)."""
    from quantlab.research.alpha.profiles import scanner_family_catalog
    from quantlab.research.alpha.venues import list_venue_capabilities

    families = scanner_family_catalog()
    auto_row = {
        "name": "auto",
        "family": "auto",
        "version": "profiles-v1",
        "label_es": "Auto — que recomiende",
        "description": (
            "Sin dirigir familia: scorea con perfil equilibrado e infiere "
            "familia + estrategias + TF para el conjunto."
        ),
        "scoring_profile": "balanced",
        "factors": [],
        "auto_mode": True,
    }
    return {
        "ok": True,
        "profiles": [auto_row, *families],
        "venues": [c.to_dict() for c in list_venue_capabilities()],
        "symbol_batches": list(SCANNER_SYMBOL_BATCHES),
        "symbol_limit_all": SYMBOL_LIMIT_ALL,
        "symbol_limit_min": SYMBOL_LIMIT_MIN,
        "symbol_limit_max": SYMBOL_LIMIT_MAX,
        "top_n_min": SCANNER_TOP_N_MIN,
        "top_n_max": SCANNER_TOP_N_MAX,
        "default_profile": "auto",
        "default_symbol_limit": 30,
        "note": (
            "Elegí Auto para que el scanner proponga familia/estrategias/TF, "
            "o una rama fija del Simulador. "
            f"Cantidad de monedas libre ({SYMBOL_LIMIT_MIN}–{SYMBOL_LIMIT_MAX}), "
            f"{SYMBOL_LIMIT_ALL}=todas, o lista puntual. "
            f"Top ranking {SCANNER_TOP_N_MIN}–{SCANNER_TOP_N_MAX}. "
            "Score ≠ rentabilidad."
        ),
    }


def run_binance_lab_backtest_batch(
    *,
    symbols: Sequence[str],
    strategy_id: str = "momentum",
    params: dict[str, Any] | None = None,
    interval: str = "1h",
    kline_limit: int = 24,
    experiment_id_prefix: str = "wb-bn-bt",
    reports_dir: Path | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Backtest la misma estrategia sobre varios símbolos Binance (MD público)."""
    from quantlab.brokers.binance.public_md import (
        DEFAULT_BASE_URL,
        fetch_universe_bars,
        validate_kline_interval,
    )

    if not symbols:
        raise ValidationError("symbols vacío")
    if len(symbols) > 10:
        raise ValidationError("máximo 10 símbolos por batch")
    if kline_limit < LAB_KLINE_LIMIT_MIN or kline_limit > LAB_KLINE_LIMIT_MAX:
        raise ValidationError(
            f"kline_limit debe estar entre {LAB_KLINE_LIMIT_MIN} y {LAB_KLINE_LIMIT_MAX}"
        )
    interval = validate_kline_interval(interval)
    prefix = validate_experiment_id(experiment_id_prefix)

    url = base_url or DEFAULT_BASE_URL
    norm = [s.strip().upper() for s in symbols if s.strip()]
    bars_by_symbol = fetch_universe_bars(
        norm,
        interval=interval,
        kline_limit=kline_limit,
        base_url=url,
    )
    if not bars_by_symbol:
        raise ValidationError("sin klines para backtest batch")

    runs: list[dict[str, Any]] = []
    for sym in norm:
        sym_bars = bars_by_symbol.get(sym)
        if not sym_bars:
            runs.append({"symbol": sym, "ok": False, "error": "sin klines"})
            continue
        eid = f"{prefix}-{sym}"[:120]
        try:
            bt = run_lab_backtest(
                strategy_id=strategy_id,
                params=params,
                bars=sym_bars,
                instrument_id=f"BN:{sym}",
                data_source="binance_klines",
                experiment_id=eid,
                reports_dir=reports_dir,
            )
            runs.append({"symbol": sym, "ok": True, "result": bt})
        except ValidationError as exc:
            runs.append({"symbol": sym, "ok": False, "error": str(exc)})

    ok_runs = [r for r in runs if r.get("ok")]
    return {
        "ok": len(ok_runs) > 0,
        "kind": "binance_backtest_batch",
        "venue": "binance",
        "strategy_id": normalize_strategy_id(strategy_id),
        "interval": interval,
        "kline_limit": kline_limit,
        "n_requested": len(norm),
        "n_ok": len(ok_runs),
        "runs": runs,
        "read_only": True,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }


def run_binance_lab_pipeline(
    *,
    strategy_id: str = "momentum",
    params: dict[str, Any] | None = None,
    top_n: int = 5,
    symbol_limit: int = 15,
    interval: str = "1h",
    kline_limit: int = 24,
    experiment_id_prefix: str = "wb-bn-pipe",
    reports_dir: Path | None = None,
    base_url: str | None = None,
    walk_forward: bool = True,
    rank_fraction: float = 0.70,
    profile: str = "legacy_v1",
) -> dict[str, Any]:
    """Scan alpha Binance → backtest top-N.

    Por defecto ``walk_forward=True``: ranking en la 1ª fracción de barras y
    backtest en el tramo posterior (sin overlap), para reducir selección in-sample.
    """
    from quantlab.brokers.binance.public_md import (
        DEFAULT_BASE_URL,
        BinancePublicMdClient,
        fetch_universe_bars,
        validate_kline_interval,
    )
    from quantlab.research.alpha.quality import EligibilityConfig
    from quantlab.research.alpha.universe import (
        build_universe_from_symbol_bars,
        exclusion_reason_counts,
    )

    _validate_top_n(top_n)
    _validate_symbol_limit(symbol_limit)
    if kline_limit < LAB_KLINE_LIMIT_MIN or kline_limit > LAB_KLINE_LIMIT_MAX:
        raise ValidationError(
            f"kline_limit debe estar entre {LAB_KLINE_LIMIT_MIN} y {LAB_KLINE_LIMIT_MAX}"
        )
    if walk_forward and kline_limit < 16:
        raise ValidationError(
            "walk_forward requiere kline_limit >= 16 (rank+backtest mínimos)"
        )
    interval = validate_kline_interval(interval)
    validate_experiment_id(experiment_id_prefix)
    profile_key = (profile or "legacy_v1").strip().lower()

    url = base_url or DEFAULT_BASE_URL
    client = BinancePublicMdClient(base_url=url)
    fetch_cap = _fetch_cap_for_limit(symbol_limit, venue="binance", market_type="spot")
    symbols = client.list_spot_symbols(quote="USDT", limit=fetch_cap)
    if not symbols:
        raise ValidationError("sin símbolos USDT de Binance")

    bars_by_symbol = fetch_universe_bars(
        symbols,
        interval=interval,
        kline_limit=kline_limit,
        base_url=url,
    )
    fetch_failures = {
        s: "klines omitidas o inválidas" for s in symbols if s not in bars_by_symbol
    }
    built = build_universe_from_symbol_bars(
        venue="binance",
        symbols=symbols,
        bars_by_symbol=bars_by_symbol,
        network="mainnet",
        market_type="spot",
        instrument_prefix="BN:",
        eligibility_config=EligibilityConfig(min_bars=3, min_completeness=0.5),
        fetch_failures=fetch_failures,
    )
    universe = built.eligible_bars
    if not universe:
        raise ValidationError("ningún símbolo elegible tras filtros de calidad")

    symbol_map = {
        inst.normalized_instrument: inst.original_symbol for inst in built.instruments
    }
    wf_meta: dict[str, Any]

    if walk_forward:
        from quantlab.research.alpha.walk_forward import split_bars_walk_forward

        try:
            split = split_bars_walk_forward(universe, rank_fraction=rank_fraction)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rank_universe = split.rank_bars
        bt_universe = split.backtest_bars
        wf_meta = {"enabled": True, **split.to_dict()}
    else:
        rank_universe = universe
        bt_universe = universe
        wf_meta = {
            "enabled": False,
            "note": (
                "Misma ventana para ranking y backtest (selección in-sample). "
                "Preferí walk_forward=True."
            ),
        }

    # Ranking
    if profile_key in ("legacy_v1", "legacy"):
        result = AlphaScanner().scan(rank_universe, top_n=top_n, min_bars=3)
        selected_iids = list(result.selected)
        scores_out = [dataclass_to_dict(s) for s in result.scores]
        profile_key = "legacy_v1"
    else:
        from quantlab.research.alpha.profiles import build_profile, score_with_profile

        try:
            build_profile(profile_key)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rows = score_with_profile(rank_universe, profile_key)
        ranked = [r for r in rows if not r.excluded]
        selected_iids = [r.instrument_id for r in ranked[: max(0, top_n)]]
        scores_out = [
            {
                "instrument_id": r.instrument_id,
                "composite": r.composite,
                "components": [
                    {
                        "name": c.name,
                        "raw": c.raw,
                        "normalized": c.normalized,
                        "weight": c.weight,
                        "contribution": c.contribution,
                        "available": c.available,
                    }
                    for c in r.components
                ],
            }
            for r in ranked
        ]

    selected_symbols = [symbol_map.get(iid, iid) for iid in selected_iids]
    scan_payload: dict[str, Any] = {
        "ok": True,
        "kind": "binance_scanner",
        "venue": "binance",
        "top_n": top_n,
        "symbol_limit": symbol_limit,
        "interval": interval,
        "kline_limit": kline_limit,
        "fetched": len(symbols),
        "eligible": len(universe),
        "excluded": len(built.exclusions),
        "exclusion_counts": exclusion_reason_counts(built.exclusions),
        "exclusions": [e.to_dict() for e in built.exclusions],
        "selected": selected_iids,
        "selected_symbols": selected_symbols,
        "scores": scores_out,
        "profile": profile_key,
        "walk_forward": wf_meta,
        "read_only": True,
        "live_routing": False,
        "note": (
            "Un score alto indica adecuación al perfil seleccionado, "
            "no rentabilidad garantizada."
        ),
    }
    # Kronos SOLO con rank_universe (anti-leakage OOS).
    scan_payload = _apply_kronos_enrichment(
        scan_payload,
        rank_universe,
        profile=profile_key,
        interval=interval,
        kronos=None,
        persist_dir=reports_dir,
    )
    selected_iids = [str(x) for x in (scan_payload.get("selected") or selected_iids)]
    selected_symbols = [symbol_map.get(iid, iid) for iid in selected_iids]
    scan_payload["selected"] = selected_iids
    scan_payload["selected_symbols"] = selected_symbols

    if not selected_symbols:
        return {
            "ok": False,
            "kind": "binance_pipeline",
            "error": "scanner sin selección",
            "scanner": scan_payload,
            "walk_forward": wf_meta,
            "live_routing": False,
        }

    from quantlab.research.alpha.individual_export import (
        attach_individual_signals,
        score_row_to_signal,
        scores_to_ranked_signals,
    )
    from quantlab.research.alpha.validation.validate_candidate import (
        default_trials_path,
        validate_candidate,
    )

    scan_payload = attach_individual_signals(scan_payload)
    ranked_sigs = scores_to_ranked_signals(
        [s for s in (scan_payload.get("scores") or []) if isinstance(s, dict)],
        profile=profile_key,
        timeframe=interval,
        lookback=kline_limit,
    )
    sig_by_iid = {s.symbols[0]: s for s in ranked_sigs if s.symbols}

    trials_path = default_trials_path(reports_dir) if reports_dir is not None else None
    validation_results: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    for iid, sym in zip(selected_iids, selected_symbols, strict=True):
        sym_bars = bt_universe.get(iid)
        if not sym_bars:
            runs.append({"symbol": sym, "ok": False, "error": "sin barras OOS"})
            continue
        sig = sig_by_iid.get(iid)
        if sig is None:
            sig = score_row_to_signal(
                {"instrument_id": iid, "composite": 0.0},
                signal_type=profile_key,
                timeframe=interval,
                lookback=kline_limit,
            )
        full_bars = universe.get(iid) or sym_bars
        vr = validate_candidate(
            sig,
            strategy_id=strategy_id,
            params=params,
            bars=full_bars,
            ledger_path=trials_path,
            venue="binance",
            market_type="spot",
        )
        validation_results.append(vr.to_dict())
        runs.append(
            {
                "symbol": sym,
                "ok": vr.ok,
                "error": vr.error,
                "validation": vr.to_dict(),
            }
        )

    ok_runs = [r for r in runs if r.get("ok")]
    batch = {
        "ok": len(ok_runs) > 0,
        "kind": "binance_backtest_batch",
        "venue": "binance",
        "strategy_id": normalize_strategy_id(strategy_id),
        "interval": interval,
        "kline_limit": kline_limit,
        "n_requested": len(selected_symbols),
        "n_ok": len(ok_runs),
        "runs": runs,
        "walk_forward": wf_meta,
        "read_only": True,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
        "note": "Validación vía validate_candidate (embargo + ledger).",
    }
    return {
        "ok": batch.get("ok") is True,
        "kind": "binance_pipeline",
        "venue": "binance",
        "strategy_id": batch.get("strategy_id"),
        "scanner": scan_payload,
        "candidates": scan_payload.get("signals") or [],
        "validation_results": validation_results,
        "backtests": batch,
        "walk_forward": wf_meta,
        "read_only": True,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
        "note": (
            "Ranking A = scanner.scores/signals (sin Sharpe). "
            "Ranking B = validation_results con DSR. No mezclar."
        ),
    }


def list_lab_experiments(registry_path: Path) -> dict[str, Any]:
    """Lista ExperimentRegistry (crea DB vacía si no existe)."""
    registry = ExperimentRegistry(registry_path)
    rows = registry.list()
    experiments = [
        {
            "experiment_id": r.experiment_id,
            "status": r.status.value,
            "dataset_id": r.dataset_id,
            "strategy_version": r.strategy_version,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            "artifact_paths": list(r.artifact_paths),
            "metadata": dict(r.metadata),
        }
        for r in rows
    ]
    return {
        "ok": True,
        "kind": "experiments",
        "path": str(registry_path),
        "count": len(experiments),
        "experiments": experiments,
        "live_routing": False,
    }


def ensure_demo_experiment(registry_path: Path) -> None:
    """Si el registry está vacío, inserta un draft demo (idempotente)."""
    registry = ExperimentRegistry(registry_path)
    if registry.list():
        return
    registry.create(
        experiment_id="wb-demo-exp",
        dataset_id="wb-synthetic",
        strategy_version="momentum-demo-1",
        metadata={"source": "workbench-lab", "live_routing": False},
    )


def _metric_float(metrics: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    raw = metrics.get(key, default)
    return float(raw) if isinstance(raw, (int, float)) else default


def run_lab_optimize(
    *,
    lookbacks: tuple[int, ...] = (2, 3),
    quantities: tuple[str, ...] = ("1",),
    n_bars: int = 20,
    persist: bool = False,
    optimizer_root: Path | None = None,
    mode: str = "synthetic",
    venue: str | None = None,
    underlying: str | None = None,
    market_type: str = "futures",
    interval: str = "1h",
    period_days: int | float | str | None = None,
    initial_cash: Decimal | None = None,
) -> dict[str, Any]:
    """Grid mini: lookback × quantity → sharpe (+ Pareto sharpe/MDD) — F33.

    ``mode=historical`` (o venue+moneda): velas MD público como Backtest/Sim.
    ``mode=synthetic``: velas inventadas (debug; n_bars 8–60).

    Si ``persist`` y ``optimizer_root``: escribe summary en session ``optimizer/``.
    """
    from quantlab.brokers.md_router import fetch_bars_for_instrument
    from quantlab.research.sim.fee_schedules import (
        fee_model_from_schedule,
        get_fee_schedule,
        schedule_to_lab_fee_dict,
    )
    from quantlab.research.sim.period_bars import estimate_n_bars

    if len(lookbacks) * len(quantities) > 12:
        raise ValidationError("grid demasiado grande (máx 12 trials)")

    mode_norm = str(mode or "synthetic").strip().lower()
    v_in = str(venue or "").strip().lower()
    coin_in = str(underlying or "").strip().upper()
    use_historical = mode_norm in ("historical", "market", "real") or (
        bool(v_in)
        and bool(coin_in)
        and mode_norm not in ("synthetic", "synth", "lab")
    )

    fee_model: Any = binance_spot_fee_model()
    fee_dict: dict[str, Any] | None = None
    context: dict[str, Any]
    cash = initial_cash if initial_cash is not None else Decimal("50000")
    if cash <= 0:
        raise ValidationError("initial_cash debe ser > 0")

    if use_historical:
        if not v_in or not coin_in:
            raise ValidationError(
                "optimize histórico: venue y moneda (underlying) requeridos"
            )
        mt = str(market_type or "futures").strip().lower()
        if mt not in ("spot", "futures"):
            raise ValidationError("market_type debe ser spot o futures")
        iv = str(interval or "1h").strip()
        period_meta: dict[str, Any] | None = None
        if period_days is not None and str(period_days).strip() != "":
            period_meta = estimate_n_bars(period_days=period_days, interval=iv)
            kline_limit = int(period_meta["n_bars"])
        else:
            kline_limit = int(n_bars)
        # Tope práctico para grid (trials × velas).
        opt_bars_max = 5_000
        kline_limit = max(
            LAB_KLINE_LIMIT_MIN, min(kline_limit, LAB_KLINE_LIMIT_MAX, opt_bars_max)
        )
        resolved, bars_raw = fetch_bars_for_instrument(
            coin_in,
            venue=v_in,
            market_type=mt,
            interval=iv,
            kline_limit=kline_limit,
        )
        if len(bars_raw) < 8:
            raise ValidationError(
                f"insuficientes velas para {v_in}/{coin_in} ({len(bars_raw)}); "
                "probá otro período/TF"
            )
        bars = (
            bars_raw[-kline_limit:]
            if len(bars_raw) > kline_limit
            else list(bars_raw)
        )
        n_used = len(bars)
        fee_sched = get_fee_schedule(v_in, mt)
        fee_model = fee_model_from_schedule(fee_sched)
        fee_dict = schedule_to_lab_fee_dict(fee_sched)
        if initial_cash is None:
            cash = Decimal("10000")
        bar_range = {
            "start": bars[0].timestamp_open.isoformat(),
            "end": bars[-1].timestamp_close.isoformat(),
            "n_bars": n_used,
            "interval": bars[0].timeframe,
        }
        context = {
            "mode": "historical",
            "venue": v_in,
            "underlying": resolved.underlying,
            "market_type": mt,
            "interval": iv,
            "period_days": period_meta.get("period_days") if period_meta else None,
            "n_bars": n_used,
            "data_source": f"{v_in}_{mt}_klines",
            "instrument_id": resolved.instrument_id,
            "symbol": getattr(resolved, "symbol", None) or coin_in,
            "bar_range": bar_range,
            "strategy_family": "momentum",
        }
        data_source = context["data_source"]
    else:
        if n_bars < 8 or n_bars > 60:
            raise ValidationError("n_bars debe estar entre 8 y 60 (modo sintético)")
        bars = make_synthetic_bars(n_bars)
        n_used = n_bars
        data_source = "synthetic"
        context = {
            "mode": "synthetic",
            "data_source": "synthetic",
            "n_bars": n_used,
            "note": "Velas inventadas del lab — no es mercado real",
            "strategy_family": "momentum",
        }

    second_objective: list[float] = []
    trial_metrics: list[dict[str, float]] = []

    def objective(params: dict[str, Any]) -> float:
        strategy = maybe_wrap_for_bar_backtest(
            "momentum",
            SimpleMomentumStrategy(
                {
                    "lookback": int(params["lookback"]),
                    "quantity": str(params["quantity"]),
                }
            ),
        )
        bt = BarBacktester(
            BarBacktestConfig(experiment_id="wb-opt", initial_cash=cash),
            fee_model=fee_model,
        )
        result = bt.run(strategy, bars)
        m = result.metrics.metrics
        sharpe = _metric_float(m, "sharpe")
        mdd = _metric_float(m, "max_drawdown")
        second_objective.append(mdd)
        trial_metrics.append({"sharpe": sharpe, "max_drawdown": mdd})
        return sharpe

    space: dict[str, list[Any]] = {
        "lookback": list(lookbacks),
        "quantity": list(quantities),
    }
    opt = GridSearchOptimizer(seed=42)
    result = opt.grid(space, objective, maximize=True)

    history: list[dict[str, Any]] = []
    for i, t in enumerate(result.history):
        metrics = trial_metrics[i] if i < len(trial_metrics) else {}
        history.append(
            {
                "params": t.params,
                "score": t.score,
                "trial_id": t.trial_id,
                "metrics": metrics,
            }
        )

    pareto_payload: dict[str, Any] | None = None
    if len(result.history) >= 2 and len(second_objective) == len(result.history):
        front = pareto_from_trials(
            result.history,
            second_objective=second_objective,
            maximize=(True, False),
        )
        pareto_payload = {
            "objectives": [
                {"key": "sharpe", "direction": "max"},
                {"key": "max_drawdown", "direction": "min"},
            ],
            "n_front": len(front.front),
            "n_dominated": len(front.dominated),
            "front": [
                {
                    "trial_id": p.trial_id,
                    "params": p.params,
                    "objectives": {
                        "sharpe": p.objectives[0],
                        "max_drawdown": p.objectives[1],
                    },
                }
                for p in front.front
            ],
            "dominated": [
                {
                    "trial_id": p.trial_id,
                    "params": p.params,
                    "objectives": {
                        "sharpe": p.objectives[0],
                        "max_drawdown": p.objectives[1],
                    },
                }
                for p in front.dominated
            ],
        }

    best_metrics: dict[str, float] = {}
    for row in history:
        if row["trial_id"] == result.best.trial_id:
            raw_m = row.get("metrics") or {}
            if isinstance(raw_m, dict):
                best_metrics = {
                    str(k): float(v)
                    for k, v in raw_m.items()
                    if isinstance(v, (int, float))
                }
            break

    payload: dict[str, Any] = {
        "ok": True,
        "kind": "optimize",
        "method": result.method,
        "mode": context["mode"],
        "n_bars": n_used,
        "data_source": data_source,
        "params": {
            "lookbacks": list(lookbacks),
            "quantities": list(quantities),
        },
        "n_trials": len(result.history),
        "best": {
            "params": result.best.params,
            "score": result.best.score,
            "trial_id": result.best.trial_id,
            "metrics": best_metrics,
        },
        "history": history,
        "pareto": pareto_payload,
        "context": context,
        "initial_cash": str(cash),
        "persisted": False,
        "run_id": None,
        "path": None,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }
    if fee_dict is not None:
        payload["fee_schedule"] = fee_dict
    if use_historical:
        payload["venue"] = context.get("venue")
        payload["underlying"] = context.get("underlying")
        payload["market_type"] = context.get("market_type")
        payload["interval"] = context.get("interval")
        payload["period_days"] = context.get("period_days")
        payload["instrument_id"] = context.get("instrument_id")
        payload["bar_range"] = context.get("bar_range")

    if persist:
        if optimizer_root is None:
            raise ValidationError("optimizer_root requerido para persist=True")
        if not LIVE_BLOCKED:
            raise ValidationError(
                "LIVE_BLOCKED debe ser True; abortando optimizer persist"
            )
        payload = persist_optimizer_run(Path(optimizer_root), payload)
    return payload


def _mc_sim_with_compare_overlay(
    sim: SimulationResult,
    *,
    initial_cash: Decimal,
    leverage: Decimal,
    simulate_liquidation: bool,
    apply_funding: bool,
    funding_rates: Sequence[Decimal] | None,
) -> Any:
    """Aplica el mismo overlay post-backtest que Comparar (PnL×L, liq, funding).

    No calibra el resultado hacia el % histórico: solo reutiliza el motor.
    """
    from types import SimpleNamespace

    from quantlab.core.types.results import EquityPoint
    from quantlab.research.sim.leverage_overlay import (
        LeverageOverlayConfig,
        apply_leverage_overlay,
    )

    curve = sim.equity_curve
    if not curve:
        return sim
    lev = leverage if leverage >= Decimal("1") else Decimal("1")
    # Comparar siempre pasa por overlay; a 1x sin funding es identidad.
    if (
        lev == Decimal("1")
        and not (apply_funding and funding_rates)
        and not simulate_liquidation
    ):
        return sim

    bt_dict: dict[str, Any] = {
        "initial_equity": str(initial_cash),
        "final_equity": str(curve[-1].equity),
        "equity_curve_tail": [
            {"ts": p.timestamp.isoformat(), "equity": str(p.equity)} for p in curve
        ],
    }
    rates: list[Decimal] | None = None
    if apply_funding and funding_rates:
        rates = list(funding_rates)[: len(curve)]
        if len(rates) < len(curve):
            rates = rates + [Decimal("0")] * (len(curve) - len(rates))

    overlay = apply_leverage_overlay(
        bt_dict,
        config=LeverageOverlayConfig(
            leverage=lev,
            simulate_liquidation=simulate_liquidation,
            apply_funding=apply_funding,
        ),
        funding_rates=rates,
    )
    out_curve = overlay.get("equity_curve") or []
    new_points: list[EquityPoint] = []
    for i, item in enumerate(out_curve):
        if not isinstance(item, Mapping):
            continue
        ts = curve[i].timestamp if i < len(curve) else curve[-1].timestamp
        new_points.append(
            EquityPoint(timestamp=ts, equity=Decimal(str(item["equity"])))
        )
    if not new_points:
        return sim
    return SimpleNamespace(
        equity_curve=tuple(new_points),
        fills=sim.fills,
        liquidated=bool(overlay.get("liquidated")),
        total_funding=str(overlay.get("total_funding") or "0"),
    )


def _mc_cash_from_sim_context(
    sim_context: Mapping[str, Any],
) -> tuple[str, Decimal, Decimal]:
    """Capital de trabajo MC = misma caja que Comparar.

    - ``fixed``: usa ``initial_capital`` (obligatorio).
    - ``unconstrained``: usa ``run_cash`` si viene; si no,
      ``max(per_trade × 50, 10000)`` (misma fórmula que compare.py).
    """
    capital_mode = str(sim_context.get("capital_mode") or "fixed").strip().lower()
    if capital_mode not in ("fixed", "unconstrained"):
        capital_mode = "fixed"

    def _dec_field(raw: Any, *, field: str, default: str | None = None) -> Decimal:
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            if default is None:
                raise ValidationError(f"sim_context: {field} requerido")
            raw = default
        try:
            return Decimal(str(raw).strip())
        except Exception as exc:
            raise ValidationError(
                f"sim_context {field} inválido: {raw!r}"
            ) from exc

    per_trade = _dec_field(
        sim_context.get("per_trade_usd"),
        field="per_trade_usd",
        default="1000",
    )
    if per_trade <= 0:
        raise ValidationError("sim_context: per_trade_usd debe ser > 0")

    if capital_mode == "fixed":
        ic_raw = sim_context.get("initial_capital")
        if ic_raw is None or (isinstance(ic_raw, str) and not str(ic_raw).strip()):
            # Compat: algunos handoffs guardan solo run_cash.
            ic_raw = sim_context.get("run_cash")
        initial_cash = _dec_field(ic_raw, field="initial_capital")
    else:
        run_raw = sim_context.get("run_cash")
        if run_raw is not None and str(run_raw).strip() != "":
            initial_cash = _dec_field(run_raw, field="run_cash")
        else:
            # Misma caja lab que research.sim.compare (sin monto).
            initial_cash = max(per_trade * Decimal("50"), Decimal("10000"))

    if initial_cash <= 0:
        raise ValidationError("sim_context: capital de trabajo debe ser > 0")
    return capital_mode, initial_cash, per_trade


def _resolve_mc_from_sim_context(
    sim_context: Mapping[str, Any],
    *,
    n_bars: int,
    strategy_id_fallback: str,
) -> dict[str, Any]:
    """Resuelve velas + estrategia + capital desde el handoff del Simulador."""
    from quantlab.brokers.md_router import fetch_bars_for_instrument
    from quantlab.montecarlo.limits import MAX_BARS, MIN_BARS
    from quantlab.research.sim.fee_schedules import (
        fee_model_from_schedule,
        get_fee_schedule,
        schedule_to_lab_fee_dict,
    )
    from quantlab.research.sim.period_bars import estimate_n_bars

    pairs_raw = sim_context.get("pairs")
    if not isinstance(pairs_raw, list) or not pairs_raw:
        raise ValidationError(
            "sim_context sin pairs: abrí Monte Carlo desde el Simulador "
            "con moneda y mercado elegidos"
        )
    first = pairs_raw[0]
    if not isinstance(first, dict):
        raise ValidationError("sim_context.pairs[0] inválido")
    venue = str(first.get("venue", "")).strip().lower()
    underlying = str(
        first.get("underlying") or first.get("ticker") or ""
    ).strip()
    if not venue or not underlying:
        raise ValidationError(
            "sim_context: cada pair requiere venue + underlying/ticker"
        )

    market_type = str(sim_context.get("market_type") or "futures").strip().lower()
    if market_type not in ("spot", "futures"):
        market_type = "futures"
    interval = str(sim_context.get("interval") or "1h").strip()
    period_days = sim_context.get("period_days")

    # Horizonte: fidelidad al período Comparar (hasta MAX_BARS).
    # No calibra el PnL histórico — solo alinea la ventana de velas.
    effective_n = max(MIN_BARS, min(int(n_bars), MAX_BARS))
    sim_bars_est: int | None = None
    horizon_warning: str | None = None
    if period_days is not None:
        try:
            est = estimate_n_bars(period_days=period_days, interval=interval)
            sim_bars_est = int(est["n_bars"])
            target = min(MAX_BARS, max(sim_bars_est, MIN_BARS))
            if effective_n < target:
                horizon_warning = (
                    f"Horizonte MC alineado al período Comparar: "
                    f"{effective_n}→{target} velas (tope {MAX_BARS}). "
                    f"Estimado Comparar ≈{sim_bars_est} "
                    f"({period_days}d × {interval}). "
                    "MC estresa esa ventana con ruido; "
                    "no calibra al % de la tabla HISTÓRICO."
                )
                effective_n = target
            elif sim_bars_est > MAX_BARS:
                horizon_warning = (
                    f"Comparar ≈{sim_bars_est} velas; MC usa tope {MAX_BARS}. "
                    "Ventana más corta que el histórico completo."
                )
        except (ValidationError, KeyError, TypeError, ValueError):
            pass

    kline_limit = max(effective_n, LAB_KLINE_LIMIT_MIN)
    if sim_bars_est is not None:
        kline_limit = max(kline_limit, min(sim_bars_est, LAB_KLINE_LIMIT_MAX))
    kline_limit = max(LAB_KLINE_LIMIT_MIN, min(kline_limit, LAB_KLINE_LIMIT_MAX))

    resolved, bars = fetch_bars_for_instrument(
        underlying,
        venue=venue,
        market_type=market_type,
        interval=interval,
        kline_limit=kline_limit,
    )
    if len(bars) < 4:
        raise ValidationError(
            f"sim_context: insuficientes velas para {venue}/{underlying} "
            f"(got {len(bars)})"
        )
    run_bars = bars[-effective_n:] if len(bars) > effective_n else list(bars)

    sid_raw = (
        str(sim_context.get("strategy_id") or strategy_id_fallback or "momentum")
        .strip()
    )
    sid = normalize_strategy_id(sid_raw)
    caller_params = sim_context.get("strategy_params")
    caller = dict(caller_params) if isinstance(caller_params, dict) else {}
    if sid == "momentum" and "lookback" not in caller:
        caller["lookback"] = 2
    strategy_params = merge_default_params(sid, caller)
    strategy = maybe_wrap_for_bar_backtest(sid, _build_strategy(sid, strategy_params))

    # Misma caja que Comparar: fixed → initial_capital; sin monto → run_cash lab.
    capital_mode, initial_cash, per_trade_usd = _mc_cash_from_sim_context(
        sim_context
    )
    # Congelar capital efectivo en el contexto (memo / UI / reopen).
    sim_ctx_out = dict(sim_context)
    sim_ctx_out["capital_mode"] = capital_mode
    sim_ctx_out["per_trade_usd"] = str(per_trade_usd)
    if capital_mode == "fixed":
        sim_ctx_out["initial_capital"] = str(initial_cash)
    sim_ctx_out["run_cash"] = str(initial_cash)

    # Mismos toggles de ejecución que Comparar (motor), sin forzar el PnL.
    try:
        leverage = Decimal(str(sim_context.get("leverage") or "1"))
    except Exception:
        leverage = Decimal("1")
    if leverage < Decimal("1"):
        leverage = Decimal("1")
    if leverage > Decimal("125"):
        leverage = Decimal("125")
    simulate_liquidation = bool(
        sim_context.get(
            "liq",
            sim_context.get("simulate_liquidation", True),
        )
    )
    apply_funding = bool(
        sim_context.get(
            "funding",
            sim_context.get("apply_funding", True),
        )
    )
    sim_ctx_out["leverage"] = str(leverage)
    sim_ctx_out["liq"] = simulate_liquidation
    sim_ctx_out["funding"] = apply_funding
    sim_ctx_out["simulate_liquidation"] = simulate_liquidation
    sim_ctx_out["apply_funding"] = apply_funding

    fee_sched = get_fee_schedule(venue, market_type)
    fee_model = fee_model_from_schedule(fee_sched)
    fee_dict = schedule_to_lab_fee_dict(fee_sched)

    return {
        "bars": run_bars,
        "strategy": strategy,
        "strategy_id": sid,
        "strategy_params": strategy_params,
        "initial_cash": initial_cash,
        "per_trade_usd": per_trade_usd,
        "capital_mode": capital_mode,
        "leverage": leverage,
        "simulate_liquidation": simulate_liquidation,
        "apply_funding": apply_funding,
        "resolved": resolved,
        "equity_currency": "USDT",
        "fee_model": fee_model,
        "fee_dict": fee_dict,
        "venue": venue,
        "market_type": market_type,
        "interval": interval,
        "instrument_id": resolved.instrument_id,
        "underlying": resolved.underlying,
        "data_source": f"{venue}_{market_type}",
        "pairs_count": len(pairs_raw),
        "summary_line": str(sim_context.get("summary_line") or ""),
        "sim_context": sim_ctx_out,
        "horizon_warning": horizon_warning,
        "sim_bars_estimate": sim_bars_est,
        "n_bars_effective": len(run_bars),
    }


def run_lab_montecarlo(
    *,
    n_scenarios: int = 1000,
    n_bars: int = 60,
    noise_bps: float = 10.0,
    seed: int = 42,
    persist: bool = True,
    montecarlo_root: Path | None = None,
    session_id: str | None = None,
    scan_id: str | None = None,
    backtest_id: str | None = None,
    strategy_id: str = "buy_once",
    store_paths: bool = False,
    max_persisted_trajectories: int = 16,
    batch_size: int = 1000,
    mode: str = "technical_lab",
    confirm_large: bool = False,
    cancellation: Any | None = None,
    on_progress: Any | None = None,
    sim_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """MC lab: sintético (demo) o ligado al Simulador via ``sim_context``.

    ``n_bars`` = velas utilizadas **por escenario**, no #escenarios.
    ``mode``:
      - ``technical_lab``: sintético permitido; contexto completo auto-rellenado.
      - ``normal``: exige ``backtest_id`` (anti-huérfano) si no hay ``sim_context``.
      - ``sim_linked``: forzado cuando hay ``sim_context`` válido (moneda real).
    """
    from quantlab.montecarlo.dataset import DatasetReference
    from quantlab.montecarlo.limits import (
        CONFIRM_EXTREME_THRESHOLD,
        CONFIRM_LARGE_THRESHOLD,
        DEFAULT_MAX_PERSISTED_TRAJECTORIES,
        estimate_cost,
        validate_n_bars,
        validate_n_scenarios,
    )
    from quantlab.montecarlo.models import METHOD_DISCLAIMER, MonteCarloConfig
    from quantlab.montecarlo.traceability import (
        build_lab_context,
        hash_bars,
        hash_mapping,
        normalize_montecarlo_payload,
    )

    validate_n_scenarios(n_scenarios)
    validate_n_bars(n_bars)
    if noise_bps < 0:
        raise ValidationError("noise_bps debe ser >= 0")
    if max_persisted_trajectories < 0:
        raise ValidationError("max_persisted_trajectories >= 0")
    if max_persisted_trajectories == 0:
        store_paths = False
    if max_persisted_trajectories > DEFAULT_MAX_PERSISTED_TRAJECTORIES * 4:
        max_persisted_trajectories = DEFAULT_MAX_PERSISTED_TRAJECTORIES * 4

    sim_linked: dict[str, Any] | None = None
    if isinstance(sim_context, Mapping) and sim_context:
        sim_linked = _resolve_mc_from_sim_context(
            sim_context,
            n_bars=n_bars,
            strategy_id_fallback=strategy_id,
        )

    mode_key = (mode or "technical_lab").strip().lower()
    if sim_linked is not None:
        mode_key = "sim_linked"
    if mode_key not in ("technical_lab", "normal", "sim_linked"):
        raise ValidationError(
            "mode debe ser 'technical_lab', 'normal' o 'sim_linked'"
        )
    if mode_key == "normal" and not backtest_id and sim_linked is None:
        raise ValidationError(
            "modo normal: se requiere backtest_id (flujo Backtest → Monte Carlo) "
            "o sim_context del Simulador"
        )
    if n_scenarios >= CONFIRM_LARGE_THRESHOLD and not confirm_large:
        raise ValidationError(
            f"n_scenarios>={CONFIRM_LARGE_THRESHOLD} requiere confirm_large=true "
            "(estimá coste y confirmá en UI)"
        )
    if n_scenarios >= CONFIRM_EXTREME_THRESHOLD and not confirm_large:
        raise ValidationError(
            "1.000.000 escenarios requiere confirmación explícita (confirm_large=true)"
        )

    size_warning = None
    if n_scenarios >= CONFIRM_LARGE_THRESHOLD:
        size_warning = (
            f"N={n_scenarios}: corrida grande — batching + memoria acotada; "
            "trayectorias limitadas a max_persisted_trajectories."
        )

    mc_strategy: Any
    if sim_linked is not None:
        bars = sim_linked["bars"]
        n_bars = len(bars)
        initial_cash = sim_linked["initial_cash"]
        equity_currency = str(sim_linked["equity_currency"])
        strategy_params = dict(sim_linked["strategy_params"])
        sid = str(sim_linked["strategy_id"])
        fee_model = sim_linked["fee_model"]
        fee_dict = dict(sim_linked["fee_dict"])
        mc_strategy = sim_linked["strategy"]
        leverage = Decimal(str(sim_linked.get("leverage") or "1"))
        simulate_liquidation = bool(sim_linked.get("simulate_liquidation", True))
        apply_funding = bool(sim_linked.get("apply_funding", True))
        funding_rates: list[Decimal] | None = None
        if apply_funding and str(sim_linked.get("market_type")) == "futures":
            try:
                from quantlab.brokers.md_router import fetch_funding_rates

                funding_rates = fetch_funding_rates(
                    sim_linked["resolved"],
                    limit=len(bars),
                )
            except Exception:
                funding_rates = None
        ds_hash = hash_bars(bars)
        first_bar = bars[0]
        last_bar = bars[-1]
        dataset_ref = DatasetReference(
            dataset_id=f"sim-{sim_linked['venue']}-{sim_linked['underlying']}",
            source=str(sim_linked["data_source"]),
            venue=str(sim_linked["venue"]),
            network="public_md",
            symbol=str(sim_linked["instrument_id"]),
            normalized_instrument=str(sim_linked["instrument_id"]),
            market_type=str(sim_linked["market_type"]),
            timeframe=str(sim_linked["interval"]),
            start_time=first_bar.timestamp_open,
            end_time=last_bar.timestamp_close,
            bars=len(bars),
            hash=ds_hash,
            storage_path=None,
            synthetic=False,
            generator_config={
                "origin": "simulator_sim_context",
                "summary_line": sim_linked.get("summary_line") or "",
                "pairs_count": sim_linked.get("pairs_count"),
                "leverage": str(leverage),
                "simulate_liquidation": simulate_liquidation,
                "apply_funding": apply_funding,
            },
            seed=seed,
        )
    else:
        bars = make_synthetic_bars(n_bars)
        initial_cash = Decimal("50000")
        equity_currency = "LAB"  # capital sintético de laboratorio (no USDT de exchange)
        strategy_params = {"quantity": "1"}
        sid = normalize_strategy_id(strategy_id) if strategy_id else "buy_once"
        fee_schedule = resolve_binance_spot_fee_schedule()
        fee_model = binance_spot_fee_model()
        fee_dict = fee_schedule.to_dict()
        mc_strategy = BuyOnceStrategy(strategy_params)
        leverage = Decimal("1")
        simulate_liquidation = False
        apply_funding = False
        funding_rates = None
        ds_hash = hash_bars(bars)
        dataset_ref = DatasetReference.from_synthetic_bars(
            bars, dataset_hash=ds_hash, seed=seed
        )

    fee_totals: list[float] = []
    fill_counts: list[int] = []

    def runner(noisy: Any) -> Any:
        if hasattr(mc_strategy, "reset"):
            with contextlib.suppress(Exception):
                mc_strategy.reset()
        bt = BarBacktester(
            BarBacktestConfig(experiment_id="wb-mc", initial_cash=initial_cash),
            fee_model=fee_model,
        )
        sim = bt.run(mc_strategy, noisy).simulation
        n_f = len(sim.fills)
        fill_counts.append(n_f)
        fee_totals.append(sum(float(f.fee.amount) for f in sim.fills))
        if sim_linked is not None:
            return _mc_sim_with_compare_overlay(
                sim,
                initial_cash=initial_cash,
                leverage=leverage,
                simulate_liquidation=simulate_liquidation,
                apply_funding=apply_funding,
                funding_rates=funding_rates,
            )
        return sim

    cfg = MonteCarloConfig(
        n_scenarios=n_scenarios,
        n_bars=n_bars,
        seed=seed,
        noise_bps=noise_bps,
        persist_result=persist,
        batch_size=batch_size,
        max_persisted_trajectories=max_persisted_trajectories,
        store_paths=store_paths,
    )
    mc = MonteCarloSimulator(seed=seed)
    result = mc.run(
        bars,
        runner,
        config=cfg,
        store_paths=store_paths,
        max_paths_stored=max_persisted_trajectories,
        initial_equity=float(initial_cash),
        batch_size=batch_size,
        retain_results=False,
        cancellation=cancellation,
        on_progress=on_progress,
    )
    mean_total_fees = sum(fee_totals) / len(fee_totals) if fee_totals else 0.0
    mean_fills = sum(fill_counts) / len(fill_counts) if fill_counts else 0.0
    mean_fee_per_fill = (
        mean_total_fees / mean_fills if mean_fills > 0 else None
    )

    orphan = (
        mode_key == "technical_lab"
        and not backtest_id
        and not scan_id
        and sim_linked is None
    )
    ctx_symbols: tuple[str, ...]
    if sim_linked is not None:
        ctx_symbols = (str(sim_linked["instrument_id"]),)
        ds_source = str(sim_linked["data_source"])
    else:
        ctx_symbols = (dataset_ref.symbol,) if dataset_ref.symbol else ("WB:SYN",)
        ds_source = "synthetic"
    ctx = build_lab_context(
        session_id=session_id,
        scan_id=scan_id,
        backtest_id=backtest_id,
        strategy_id=sid,
        strategy_params=strategy_params,
        symbols=ctx_symbols,
        timeframe=dataset_ref.timeframe,
        dataset_source=ds_source,
        dataset_id=dataset_ref.dataset_id,
        dataset_hash=ds_hash,
        initial_equity=float(initial_cash),
        fee_model=getattr(fee_model, "model_id", "fee.binance_spot_vip0.v1"),
        orphan=orphan,
    )
    ctx_dict = ctx.to_dict()
    ctx_dict["strategy_name"] = ctx_dict.get("strategy_name") or sid
    ctx_dict["lab_mode"] = mode_key
    ctx_dict["equity_currency"] = equity_currency
    if sim_linked is not None:
        ctx_dict["sim_context"] = sim_linked["sim_context"]
        ctx_dict["sim_linked"] = True
        ctx_dict["sim_summary"] = sim_linked.get("summary_line") or ""
        ctx_dict["coin"] = sim_linked.get("underlying")
        ctx_dict["venue"] = sim_linked.get("venue")
        ctx_dict["market_type"] = sim_linked.get("market_type")
        ctx_dict["capital_mode"] = sim_linked.get("capital_mode")
        ctx_dict["per_trade_usd"] = (
            str(sim_linked["per_trade_usd"])
            if sim_linked.get("per_trade_usd") is not None
            else None
        )
        ctx_dict["initial_capital"] = (
            str(sim_linked["initial_cash"])
            if sim_linked.get("capital_mode") == "fixed"
            else None
        )
        ctx_dict["run_cash"] = str(sim_linked["initial_cash"])
        ctx_dict["leverage"] = str(sim_linked.get("leverage") or "1")
        ctx_dict["simulate_liquidation"] = bool(
            sim_linked.get("simulate_liquidation", True)
        )
        ctx_dict["apply_funding"] = bool(sim_linked.get("apply_funding", True))
        if sim_linked.get("horizon_warning"):
            ctx_dict["horizon_warning"] = sim_linked["horizon_warning"]
        if sim_linked.get("sim_bars_estimate") is not None:
            ctx_dict["sim_bars_estimate"] = sim_linked["sim_bars_estimate"]
        ctx_dict["n_bars_effective"] = sim_linked.get("n_bars_effective") or n_bars
    if mode_key == "technical_lab" and orphan:
        ctx_dict["orphan_warning"] = (
            "Modo laboratorio técnico: dataset sintético WB:SYN, estrategia BuyOnce, "
            f"capital inicial {initial_cash} {equity_currency}. "
            "No es un backtest de mercado real."
        )

    cfg_dict = cfg.to_dict()
    metrics_dict = result.metrics.to_dict() if result.metrics else {}
    cost = estimate_cost(
        n_scenarios=n_scenarios,
        n_bars=n_bars,
        store_paths=store_paths,
        max_persisted_trajectories=max_persisted_trajectories,
        scenarios_per_second=result.scenarios_per_second,
    )
    capital_summary = {
        "initial_equity": float(initial_cash),
        "mean_final_equity": result.mean_equity,
        "median_final_equity": (
            result.metrics.median_equity if result.metrics else None
        ),
        "currency": equity_currency,
        "capital_mode": (sim_linked or {}).get("capital_mode") if sim_linked else None,
        "per_trade_usd": (
            str(sim_linked["per_trade_usd"])
            if sim_linked and sim_linked.get("per_trade_usd") is not None
            else None
        ),
        "min_final_equity": (
            min(result.final_equities) if result.final_equities else None
        ),
        "max_final_equity": (
            max(result.final_equities) if result.final_equities else None
        ),
    }
    fee_summary = {
        "schedule_id": fee_dict["schedule_id"],
        "as_of": fee_dict["as_of"],
        "source_url": fee_dict["source_url"],
        "maker_bps": fee_dict["maker_bps"],
        "taker_bps": fee_dict["taker_bps"],
        "maker_pct": fee_dict["maker_pct"],
        "taker_pct": fee_dict["taker_pct"],
        "fee_per_side_note": (
            f"Por operación (lado): maker {fee_dict['maker_bps']} bps "
            f"({fee_dict['maker_pct']}%) · taker {fee_dict['taker_bps']} bps "
            f"({fee_dict['taker_pct']}%)"
        ),
        "mean_total_fees": mean_total_fees,
        "mean_fills_per_scenario": mean_fills,
        "mean_fee_per_fill": mean_fee_per_fill,
        "note": fee_dict["note"],
    }
    ds_dict = dataset_ref.to_dict()
    bars_meta = {
        "label_es": "Velas utilizadas por escenario",
        "n_bars": n_bars,
        "timeframe": dataset_ref.timeframe,
        "duration_label": ds_dict.get("duration_label"),
        "start_time": ds_dict.get("start_time"),
        "end_time": ds_dict.get("end_time"),
        "tooltip_es": (
            f"Cada escenario vuelve a ejecutar la estrategia sobre estas {n_bars} "
            f"velas {dataset_ref.timeframe} perturbadas."
        ),
    }
    payload: dict[str, Any] = {
        "ok": result.status == "completed",
        "kind": "montecarlo",
        "method": cfg.method.value,
        "disclaimer": METHOD_DISCLAIMER,
        "n_scenarios": result.n_scenarios,
        "n_scenarios_requested": n_scenarios,
        "n_scenarios_completed": result.n_scenarios_completed,
        "n_scenarios_failed": result.n_scenarios_failed,
        "n_scenarios_cancelled": result.n_scenarios_cancelled,
        "n_bars": n_bars,
        "dataset_bar_count": n_bars,
        "bars_meta": bars_meta,
        "bar_horizon_label": cfg.bar_horizon_label(dataset_ref.timeframe),
        "noise_bps": float(noise_bps),
        "seed": result.seed,
        "initial_equity": float(initial_cash),
        "equity_currency": equity_currency,
        "mean_equity": result.mean_equity,
        "std_equity": result.std_equity,
        "ci_low": result.ci_low,
        "ci_high": result.ci_high,
        "ci_level": result.ci_level,
        "ci_kind": "wald_mean",
        "final_equities": list(result.final_equities),
        "sample_final_equities": (
            list(result.sample_final_equities) if result.sample_final_equities else None
        ),
        "equity_paths": (
            [list(p) for p in result.equity_paths] if result.equity_paths else None
        ),
        "max_persisted_trajectories": max_persisted_trajectories,
        "trajectories_stored": (
            len(result.equity_paths) if result.equity_paths else 0
        ),
        "storage_mode": result.storage_mode,
        "histogram": result.histogram,
        "percentiles_approximate": result.percentiles_approximate,
        "status": result.status,
        "partial": result.partial,
        "elapsed_seconds": result.elapsed_seconds,
        "scenarios_per_second": result.scenarios_per_second,
        "cost_estimate": cost,
        "dataset": ds_dict,
        "capital_summary": capital_summary,
        "fee_schedule": fee_dict,
        "fee_summary": fee_summary,
        "context": ctx_dict,
        "config": cfg_dict,
        "metrics": metrics_dict,
        "config_hash": hash_mapping(cfg_dict),
        "relations": {
            "backtest_id": ctx.backtest_id,
            "scan_id": ctx.scan_id,
            "dataset_id": ctx.dataset_id,
            "strategy_config_id": ctx.strategy_config_id,
            "strategy_params_hash": ctx.strategy_params_hash,
            "dataset_hash": ctx.dataset_hash,
            "config_hash": hash_mapping(cfg_dict),
            "code_commit": ctx.code_commit,
        },
        "mode": mode_key,
        "warnings": [
            w
            for w in (
                size_warning,
                ctx_dict.get("orphan_warning"),
                (sim_linked or {}).get("horizon_warning") if sim_linked else None,
            )
            if w
        ],
        "persisted": False,
        "run_id": None,
        "path": None,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }
    if persist and result.status == "completed" and not result.partial:
        if montecarlo_root is None:
            raise ValidationError("montecarlo_root requerido para persist=True")
        if not LIVE_BLOCKED:
            raise ValidationError(
                "LIVE_BLOCKED debe ser True; abortando montecarlo persist"
            )
        payload = persist_montecarlo_run(Path(montecarlo_root), payload)
    else:
        payload = normalize_montecarlo_payload(payload)
    # normalize reconstruye context tipado; reinyectar identidad del Simulador
    if sim_linked is not None:
        ctx_out = dict(payload.get("context") or {})
        ctx_out["sim_context"] = sim_linked["sim_context"]
        ctx_out["sim_linked"] = True
        ctx_out["sim_summary"] = sim_linked.get("summary_line") or ""
        ctx_out["coin"] = sim_linked.get("underlying")
        ctx_out["venue"] = sim_linked.get("venue")
        ctx_out["market_type"] = sim_linked.get("market_type")
        ctx_out["lab_mode"] = "sim_linked"
        ctx_out.pop("orphan_warning", None)
        ctx_out["orphan_technical_mode"] = False
        ctx_out["capital_mode"] = sim_linked.get("capital_mode")
        ctx_out["per_trade_usd"] = (
            str(sim_linked["per_trade_usd"])
            if sim_linked.get("per_trade_usd") is not None
            else None
        )
        ctx_out["initial_capital"] = (
            str(sim_linked["initial_cash"])
            if sim_linked.get("capital_mode") == "fixed"
            else None
        )
        ctx_out["run_cash"] = str(sim_linked["initial_cash"])
        ctx_out["leverage"] = str(sim_linked.get("leverage") or "1")
        ctx_out["simulate_liquidation"] = bool(
            sim_linked.get("simulate_liquidation", True)
        )
        ctx_out["apply_funding"] = bool(sim_linked.get("apply_funding", True))
        if sim_linked.get("horizon_warning"):
            ctx_out["horizon_warning"] = sim_linked["horizon_warning"]
        if sim_linked.get("sim_bars_estimate") is not None:
            ctx_out["sim_bars_estimate"] = sim_linked["sim_bars_estimate"]
        ctx_out["n_bars_effective"] = sim_linked.get("n_bars_effective") or len(
            sim_linked.get("bars") or []
        )
        payload["context"] = ctx_out
        payload["mode"] = "sim_linked"
        warnings = list(payload.get("warnings") or [])
        hw = sim_linked.get("horizon_warning")
        if hw and hw not in warnings:
            warnings.append(hw)
        warnings = [
            w
            for w in warnings
            if "sintético" not in str(w).lower() and "huérfano" not in str(w).lower()
        ]
        payload["warnings"] = warnings
    return payload


def _demo_feature_version() -> str:
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%f")[:-3] + "Z"
    return f"wb-demo-{stamp}"


def run_lab_features(
    *,
    n_bars: int = 20,
    store_root: Path | None = None,
    version: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Pipeline demo (close + simple_return + log_return) → FeatureStore sesión.

    Si ``persist`` y ``store_root``: escribe via ``FeatureStore.put`` (F31).
    """
    if n_bars < 4 or n_bars > 120:
        raise ValidationError("n_bars debe estar entre 4 y 120")
    bars = make_synthetic_bars(n_bars)
    pipeline = build_pipeline(
        ClosePriceTransformer(),
        SimpleReturnTransformer(),
        LogReturnTransformer(),
        name="wb_demo_pipeline",
    )
    frame = pipeline.run(bars)
    payload = feature_frame_to_dict(frame)
    columns = sorted(payload["series"].keys())
    # Resumen liviano para UI (sin todos los points si son muchos)
    series_summary = {
        name: {
            "min_lookback": s["min_lookback"],
            "n_points": len(s["points"]),
            "tail": s["points"][-3:] if s["points"] else [],
        }
        for name, s in payload["series"].items()
    }
    result: dict[str, Any] = {
        "ok": True,
        "kind": "features",
        "pipeline_name": frame.pipeline_name,
        "instrument_id": frame.instrument_id,
        "bar_count": frame.bar_count,
        "min_lookback": frame.min_lookback,
        "schema_version": frame.schema_version,
        "series_summary": series_summary,
        "columns": columns,
        "persisted": False,
        "store_ref": None,
        "store_path": None,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }
    if persist and store_root is not None:
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True; abortando feature persist")
        ver = (version or _demo_feature_version()).strip()
        if not ver:
            raise ValidationError("version de feature inválida")
        store = FeatureStore(Path(store_root))
        ref = store.put(frame, version=ver)
        result["persisted"] = True
        result["store_path"] = str(Path(store_root).resolve())
        result["store_ref"] = {
            "instrument_id": ref.instrument_id,
            "pipeline_name": ref.pipeline_name,
            "version": ref.version,
            "path": ref.path,
            "checksum": ref.checksum,
            "schema_version": ref.schema_version,
            "created_at": ref.created_at.isoformat(),
            "columns": columns,
        }
    return result


def run_lab_export_hb(
    export_root: Path,
    *,
    experiment_id: str = "wb-hb-export",
    strategy_version: str = "demo-1",
    dataset_id: str = "wb-synthetic",
) -> dict[str, Any]:
    """Validate + build + export a path bajo export_root (path-safe). LIVE routing false.

    Escribe:
    - ``{experiment_id}.json`` — alias latest (compat F21)
    - ``{export_id}.json`` — snapshot histórico único (F34)
    """
    if not LIVE_BLOCKED:
        raise ValidationError("LIVE_BLOCKED debe ser True; abortando export")
    experiment_id = validate_experiment_id(experiment_id)
    dataset_id = validate_experiment_id(dataset_id) if dataset_id else "wb-synthetic"
    export_root = export_root.resolve()
    export_root.mkdir(parents=True, exist_ok=True)

    now = datetime.now(tz=UTC)
    stamp = now.strftime("%Y%m%dT%H%M%S%f")[:-3] + "Z"
    export_id_raw = f"hb-{stamp}-{experiment_id}"
    export_id = export_id_raw[:120]
    # Fail-closed: stems path-safe
    for stem in (experiment_id, export_id):
        if "/" in stem or "\\" in stem or ".." in stem:
            raise ValidationError(f"export stem inválido: {stem!r}")

    latest_target = (export_root / f"{experiment_id}.json").resolve()
    hist_target = (export_root / f"{export_id}.json").resolve()
    for target in (latest_target, hist_target):
        try:
            target.relative_to(export_root)
        except ValueError as exc:
            raise ValidationError("path de export fuera de sandbox") from exc

    manifest = ExperimentManifest(
        experiment_id=experiment_id,
        dataset_id=dataset_id,
        dataset_version="v1",
        resolved_config={"source": "workbench", "live_routing": False},
        seed=42,
        git_commit="workbench-lab",
        python_version="3.11",
        dependency_versions_or_hash="wb-lab",
        platform="workbench",
        strategy_version=strategy_version,
        execution_model_versions=ExecutionModelVersions(
            fee_model="none",
            slippage_model="none",
            latency_model="none",
            fill_model="immediate-bar",
        ),
        artifacts_produced=(),
        created_at=now,
        checksum="a" * 64,
        status=ExperimentStatus.DRAFT,
    )
    exporter = HummingbotExporter()
    validation = exporter.validate_export(manifest)
    if not validation.ok:
        raise ValidationError("manifest inválido: " + "; ".join(validation.issues))
    package = exporter.build_execution_package(manifest)
    if package.payload.get("live_routing") is not False:
        raise ValidationError("export debe tener live_routing=false")

    # Enrich package payload for listing / wizard.
    enriched = dict(package.payload)
    enriched["export_id"] = export_id
    enriched["created_at"] = now.isoformat()
    enriched["strategy_version"] = strategy_version
    enriched["live_routing"] = False
    enriched["blocked"] = True

    hist_package = ExecutionPackage(
        experiment_id=package.experiment_id,
        strategy_version=package.strategy_version,
        payload=enriched,
    )
    latest_package = ExecutionPackage(
        experiment_id=package.experiment_id,
        strategy_version=package.strategy_version,
        payload={**enriched, "export_id": experiment_id, "is_latest_alias": True},
    )
    hist_result = exporter.export_configuration(hist_package, hist_target)
    latest_result = exporter.export_configuration(latest_package, latest_target)
    return {
        "ok": True,
        "kind": "export_hb",
        "path": hist_result.path,
        "latest_path": latest_result.path,
        "export_id": export_id,
        "checksum_note": hist_result.checksum_note,
        "live_routing": False,
        "blocked": True,
        "live_blocked": LIVE_BLOCKED is True,
        "validation_ok": validation.ok,
        "validation_issues": list(validation.issues),
        "experiment_id": package.experiment_id,
        "strategy_version": strategy_version,
        "created_at": now.isoformat(),
        "payload_keys": sorted(enriched.keys()),
        "banner": "live_routing:false — sin order routing LIVE",
        "steps": {
            "validate": {"ok": validation.ok, "issues": list(validation.issues)},
            "build": {"ok": True, "keys": sorted(enriched.keys())},
            "export": {"ok": True, "path": hist_result.path, "latest_path": latest_result.path},
        },
    }


def _segment_indices(
    bars: Sequence[Bar],
    segment: Sequence[Bar],
    *,
    offset: int = 0,
) -> dict[str, Any]:
    """Índices inclusivos del segmento respecto a ``bars`` (o offset absoluto)."""
    count = len(segment)
    if count == 0:
        return {
            "count": 0,
            "start_idx": None,
            "end_idx": None,
            "start_ts": None,
            "end_ts": None,
        }
    # Match por identidad de timestamps (serie sintética ordenada).
    start_ts = segment[0].timestamp_open
    end_ts = segment[-1].timestamp_close
    start_idx: int | None = None
    for i, bar in enumerate(bars):
        if bar.timestamp_open == start_ts:
            start_idx = offset + i
            break
    if start_idx is None:
        start_idx = offset
    end_idx = start_idx + count - 1
    return {
        "count": count,
        "start_idx": start_idx,
        "end_idx": end_idx,
        "start_ts": start_ts.isoformat(),
        "end_ts": end_ts.isoformat(),
    }


def _leakage_entry(pair: str, left: Sequence[Bar], right: Sequence[Bar]) -> dict[str, Any]:
    report = check_temporal_leakage(left, right)
    return {"pair": pair, "ok": report.ok, "issues": list(report.issues)}


def run_lab_validation(
    *,
    n_bars: int = 40,
    train_frac: float = 0.6,
    val_frac: float = 0.2,
    train_size: int = 10,
    test_size: int = 5,
    step: int | None = None,
    persist: bool = False,
    validation_root: Path | None = None,
) -> dict[str, Any]:
    """Walk-forward + train/val/OOS sobre barras sintéticas + anti-leakage (F32).

    Si ``persist`` y ``validation_root``: escribe summary en session ``validation/``.
    """
    if n_bars < 20 or n_bars > 200:
        raise ValidationError("n_bars debe estar entre 20 y 200")
    if train_size < 1 or test_size < 1:
        raise ValidationError("train_size/test_size inválidos")
    wf_step = step if step is not None else test_size
    if wf_step < 1:
        raise ValidationError("step inválido")

    bars = make_synthetic_bars(n_bars)
    split = train_val_oos_split(bars, train_frac=train_frac, val_frac=val_frac)
    folds = walk_forward(bars, train_size=train_size, test_size=test_size, step=wf_step)

    train_n = len(split.train)
    val_n = len(split.validation)
    train_seg = _segment_indices(bars, split.train)
    val_seg = _segment_indices(bars[train_n:], split.validation, offset=train_n)
    oos_seg = _segment_indices(bars[train_n + val_n :], split.oos, offset=train_n + val_n)

    # Walk-forward: índices absolutos vía start del fold.
    wf_folds: list[dict[str, Any]] = []
    start = 0
    for f in folds:
        tr = _segment_indices(bars[start:], f.train, offset=start)
        te = _segment_indices(bars[start + train_size :], f.test, offset=start + train_size)
        wf_folds.append(
            {
                "fold": f.fold,
                "train": len(f.train),
                "test": len(f.test),
                "train_idx": tr,
                "test_idx": te,
                "train_end": f.train[-1].timestamp_close.isoformat(),
                "test_start": f.test[0].timestamp_open.isoformat(),
            }
        )
        start += wf_step

    leakage_checks = [
        _leakage_entry("train_vs_validation", split.train, split.validation),
        _leakage_entry("validation_vs_oos", split.validation, split.oos),
        _leakage_entry("train_vs_oos", split.train, split.oos),
    ]
    for f in folds:
        leakage_checks.append(_leakage_entry(f"wf_fold_{f.fold}", f.train, f.test))
    n_failed = sum(1 for c in leakage_checks if not c["ok"])
    anti = {
        "ok": n_failed == 0,
        "n_checks": len(leakage_checks),
        "n_failed": n_failed,
        "checks": leakage_checks,
    }

    result: dict[str, Any] = {
        "ok": anti["ok"],
        "kind": "validation",
        "n_bars": n_bars,
        "source": "synthetic",
        "instrument_id": bars[0].instrument_id if bars else None,
        "params": {
            "train_frac": train_frac,
            "val_frac": val_frac,
            "train_size": train_size,
            "test_size": test_size,
            "step": wf_step,
        },
        "train_val_oos": {
            # Compat F21: counts planos
            "train": train_n,
            "validation": val_n,
            "oos": len(split.oos),
            "train_end": split.train[-1].timestamp_close.isoformat() if split.train else None,
            "val_start": (
                split.validation[0].timestamp_open.isoformat() if split.validation else None
            ),
            "oos_start": split.oos[0].timestamp_open.isoformat() if split.oos else None,
            "segments": {
                "train": train_seg,
                "validation": val_seg,
                "oos": oos_seg,
            },
        },
        "walk_forward": {
            "n_folds": len(folds),
            "train_size": train_size,
            "test_size": test_size,
            "step": wf_step,
            "folds": wf_folds,
        },
        "anti_leakage": anti,
        "multiple_testing": {
            "available_methods": ["bonferroni", "holm", "fdr_bh"],
            "note": (
                "APIs quantlab.validation.multiple_testing disponibles; "
                "este runner reporta splits + leakage, no p-values de estrategia"
            ),
        },
        "persisted": False,
        "run_id": None,
        "path": None,
        "live_routing": False,
        "live_blocked": LIVE_BLOCKED is True,
    }

    if persist:
        if validation_root is None:
            raise ValidationError("validation_root requerido para persist=True")
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True; abortando validation persist")
        result = persist_validation_run(Path(validation_root), result)
    return result


def lab_capabilities() -> dict[str, Any]:
    return {
        "ok": True,
        "kind": "capabilities",
        "version_module": "lab",
        "strategies": list_strategy_ids(),
        "strategy_catalog": list_strategy_catalog(),
        "features": [dict(c) for c in CAPABILITIES],
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def lab_strategies() -> dict[str, Any]:
    """GET /api/lab/strategies — catálogo con metadata + guías (F27/F115)."""
    from quantlab.workbench.strategy_guides import FAMILY_LABELS_ES

    strategies = list_strategy_catalog()
    runnable = [s["id"] for s in strategies if s.get("runnable")]
    families = sorted({str(s.get("family") or "") for s in strategies if s.get("family")})
    return {
        "ok": True,
        "kind": "strategies",
        "strategies": strategies,
        "ids": list_strategy_ids(),
        "runnable_ids": runnable,
        "families": families,
        "family_labels_es": {
            f: FAMILY_LABELS_ES.get(f, f) for f in families
        },
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "note": (
            "runnable=true → backtest/paper/Binance demo post-unlock. "
            "how_it_works = guía paso a paso para UI. "
            "LIVE producción sigue bloqueado (LIVE_BLOCKED)."
        ),
    }


def default_lab_tmpdir(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


def run_pairwise_lab_scanner(
    *,
    venue: str = "binance",
    market_type: str = "spot",
    symbol_limit: int = 20,
    interval: str = "1h",
    kline_limit: int = 720,
    detectors: tuple[str, ...] | None = None,
    top_n: int = 10,
    include_signals: bool = True,
    run_validation: bool = False,
    persist_dir: Path | None = None,
    trials_dir: Path | None = None,
    include_ml: bool = True,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Alpha Scanner modo pairwise — detectores de relación entre monedas."""
    from quantlab.brokers.binance.public_md import (
        DEFAULT_BASE_URL,
        BinancePublicMdClient,
        fetch_universe_bars,
        validate_kline_interval,
    )
    from quantlab.research.alpha.detectors.base import DetectorContext, DetectorRunConfig
    from quantlab.research.alpha.detectors.bootstrap import ensure_pairwise_detectors_loaded
    from quantlab.research.alpha.detectors.registry import global_registry
    from quantlab.research.alpha.normalization import percentile_rank_signals
    from quantlab.research.alpha.pairwise.recommend import signal_dict_with_recommendation
    from quantlab.research.alpha.quality import EligibilityConfig
    from quantlab.research.alpha.universe import build_universe_from_symbol_bars
    from quantlab.research.alpha.validation.pipeline import ValidationPipeline

    ensure_pairwise_detectors_loaded()
    v = (venue or "binance").strip().lower()
    mt = (market_type or "spot").strip().lower()
    if v not in _VENUE_SCAN_PREFIX:
        raise ValidationError(
            f"venue no soportado para pairwise: {venue!r}; "
            f"permitidos: {', '.join(sorted(_VENUE_SCAN_PREFIX))}"
        )
    if mt not in ("spot", "futures"):
        raise ValidationError("market_type debe ser spot o futures")
    if v != "binance":
        raise ValidationError(
            "pairwise scanner requiere binance (mismo venue spot/futures); "
            f"recibido {venue!r}"
        )
    _validate_symbol_limit(symbol_limit)
    if kline_limit < 120:
        raise ValidationError("pairwise scanner requiere kline_limit >= 120")
    if kline_limit < LAB_KLINE_LIMIT_MIN or kline_limit > LAB_KLINE_LIMIT_MAX:
        raise ValidationError(
            f"kline_limit debe estar entre {LAB_KLINE_LIMIT_MIN} y {LAB_KLINE_LIMIT_MAX}"
        )
    interval = validate_kline_interval(interval)
    enabled = detectors or (
        "contemporary_correlation",
        "lagged_correlation",
        "cointegration",
        "pair_spread",
    )
    prefix = _VENUE_SCAN_PREFIX[v][mt]
    fetch_cap = _fetch_cap_for_limit(symbol_limit, venue=v, market_type=mt)

    if mt == "spot":
        url = base_url or DEFAULT_BASE_URL
        client = BinancePublicMdClient(base_url=url)
        symbols = client.list_spot_symbols(quote="USDT", limit=fetch_cap)
        if not symbols:
            raise ValidationError("sin símbolos USDT de Binance spot")
        bars_by_symbol = fetch_universe_bars(
            symbols,
            interval=interval,
            kline_limit=kline_limit,
            base_url=url,
        )
    else:
        from quantlab.brokers.binance.futures_public_md import (
            DEFAULT_FUTURES_BASE_URL,
            BinanceFuturesPublicMdClient,
            fetch_futures_bars,
        )

        url = base_url or DEFAULT_FUTURES_BASE_URL
        client = BinanceFuturesPublicMdClient(base_url=url)
        symbols = client.list_futures_symbols(quote="USDT", limit=fetch_cap)
        if not symbols:
            raise ValidationError("sin símbolos USDT-M perpetuos de Binance futures")
        bars_by_symbol = fetch_futures_bars(
            symbols,
            interval=interval,
            kline_limit=kline_limit,
            base_url=url,
        )

    fetch_failures = {
        s: "klines omitidas o inválidas" for s in symbols if s not in bars_by_symbol
    }
    built = build_universe_from_symbol_bars(
        venue=v,
        symbols=symbols,
        bars_by_symbol=bars_by_symbol,
        network="mainnet",
        market_type=mt,
        instrument_prefix=prefix,
        eligibility_config=EligibilityConfig(min_bars=80, min_completeness=0.5),
        fetch_failures=fetch_failures,
    )
    universe = built.eligible_bars
    if len(universe) < 2:
        raise ValidationError("se necesitan al menos 2 símbolos elegibles para pairwise")

    ctx = DetectorContext(
        bars_by_instrument=universe,
        timeframe=interval,
        lookback_bars=min(240, kline_limit // 3),
        venue=v,
        market_type=mt,
        config={"min_bars": 80, "max_pairs": 200},
    )
    reg = global_registry()
    all_signals = reg.run_all(ctx, DetectorRunConfig(enabled=enabled))
    pipeline = ValidationPipeline()
    for det_id in enabled:
        try:
            det = reg.get(det_id)
        except ValidationError:
            continue
        det_sigs = tuple(s for s in all_signals if s.signal_type == det.signal_type)
        if det_sigs:
            pipeline.log_detection_trials(det_sigs, detector_id=det_id)
    ranked = percentile_rank_signals(all_signals)
    ranked = tuple(sorted(ranked, key=lambda s: s.normalized_score or 0.0, reverse=True))
    top = ranked[: max(0, top_n)]

    validation_results: list[dict[str, Any]] = []
    trials_path = None
    if trials_dir is not None:
        from quantlab.research.alpha.validation.validate_candidate import default_trials_path

        trials_path = default_trials_path(trials_dir)
    elif persist_dir is not None:
        from quantlab.research.alpha.validation.validate_candidate import default_trials_path

        # alpha_scans parent → experiments_dir
        trials_path = default_trials_path(persist_dir.parent)

    if run_validation and top:
        from quantlab.research.alpha.pairwise.recommend import recommend_strategy_for_signal
        from quantlab.research.alpha.validation.validate_candidate import validate_candidate

        for sig in top:
            if sig.scope.value != "pair" or len(sig.symbols) != 2:
                continue
            a, b = sig.symbols
            if a not in universe or b not in universe:
                continue
            rec = recommend_strategy_for_signal(sig.signal_type, lag=sig.lag)
            vr = validate_candidate(
                sig,
                strategy_id=rec.strategy_id,
                bars_a=universe[a],
                bars_b=universe[b],
                ledger_path=trials_path,
                venue=v,
                market_type=mt,
            )
            validation_results.append(vr.to_dict())

    payload: dict[str, Any] = {
        "ok": True,
        "kind": "pairwise_scanner",
        "venue": v,
        "market_type": mt,
        "interval": interval,
        "kline_limit": kline_limit,
        "detectors": list(enabled),
        "n_symbols": len(universe),
        "n_signals": len(all_signals),
        "top_n": top_n,
        "trial_count": pipeline.ledger.count() + len(validation_results),
        "validation_count": len(validation_results),

        "read_only": True,
        "live_blocked": LIVE_BLOCKED is True,
        "note": (
            "Señales pairwise = candidatos de investigación. "
            "Validación OOS requiere run_validation=true. "
            "No implica rentabilidad."
        ),
    }
    if include_signals:
        payload["signals"] = [signal_dict_with_recommendation(s) for s in top]
    if validation_results:
        payload["validation"] = validation_results
    if persist_dir is not None:
        from quantlab.research.alpha.persist import ScanStore

        meta = ScanStore(persist_dir).save_scored(
            profile="pairwise",
            rows=[{"signal": signal_dict_with_recommendation(s)} for s in top],
            bars_hash="pairwise",
            request={
                "detectors": list(enabled),
                "kline_limit": kline_limit,
                "venue": v,
                "market_type": mt,
            },
        )
        payload["persisted"] = meta.to_dict()
    from quantlab.research.alpha.ml.attach import attach_ml_ranking_signals

    exp = trials_dir or (persist_dir.parent if persist_dir is not None else None)
    return attach_ml_ranking_signals(payload, experiments_dir=exp, enabled=include_ml)

