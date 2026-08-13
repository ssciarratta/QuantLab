"""Validación única: candidata (individual|par) × UNA estrategia × DSR."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.research.alpha.models import AlphaSignal, SignalScope
from quantlab.research.alpha.validation.pipeline import BacktestEvalResult, ValidationPipeline
from quantlab.research.alpha.validation.trial_ledger import TrialLedger
from quantlab.research.alpha.validation.walk_forward_eval import split_bars_train_test


def default_trials_path(experiments_dir: Path) -> Path:
    return experiments_dir / "alpha_trials" / "trials.jsonl"


def _params_hash(params: Mapping[str, Any] | None) -> str:
    raw = json.dumps(params or {}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def equity_curve_to_returns(equity: Sequence[float]) -> tuple[float, ...]:
    if len(equity) < 2:
        return ()
    out: list[float] = []
    for i in range(1, len(equity)):
        prev = equity[i - 1]
        if prev == 0:
            continue
        out.append((equity[i] - prev) / prev)
    return tuple(out)


def _returns_from_backtest_payload(bt: Mapping[str, Any]) -> tuple[float, ...]:
    tail = bt.get("equity_curve_tail") or []
    eqs: list[float] = []
    for p in tail:
        if isinstance(p, Mapping) and p.get("equity") is not None:
            eqs.append(float(p["equity"]))
    return equity_curve_to_returns(eqs)


@dataclass(frozen=True, slots=True)
class ValidateCandidateResult:
    eval: BacktestEvalResult
    strategy_id: str
    params_hash: str
    scope: str
    symbols: tuple[str, ...]
    ok: bool
    error: str | None = None
    n_trials_at_eval: int = 0
    ml_feed: dict[str, Any] | None = None
    trial_id: str = ""
    opportunity_id: str | None = None
    scan_id: str | None = None
    status: str = "failed"
    pair_engine: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.eval.signal_id,
            "trial_id": self.trial_id,
            "opportunity_id": self.opportunity_id,
            "scan_id": self.scan_id,
            "strategy_id": self.strategy_id,
            "params_hash": self.params_hash,
            "scope": self.scope,
            "symbols": list(self.symbols),
            "sharpe_net": self.eval.sharpe_net,
            "deflated_sharpe": self.eval.deflated_sharpe,
            "max_drawdown": self.eval.max_drawdown,
            "n_returns": self.eval.n_returns,
            "validated": self.eval.validated,
            "ok": self.ok,
            "error": self.error,
            "status": self.status,
            "n_trials_at_eval": self.n_trials_at_eval,
            "ml_feed": dict(self.ml_feed) if self.ml_feed else None,
            "pair_engine": self.pair_engine,
        }


def _empty_eval(signal_id: str) -> BacktestEvalResult:
    return BacktestEvalResult(
        signal_id=signal_id,
        sharpe_net=0.0,
        max_drawdown=0.0,
        n_returns=0,
        deflated_sharpe=0.0,
        validated=False,
    )


def validate_candidate(
    signal: AlphaSignal,
    *,
    strategy_id: str,
    params: Mapping[str, Any] | None = None,
    bars: Sequence[Bar] | None = None,
    bars_a: Sequence[Bar] | None = None,
    bars_b: Sequence[Bar] | None = None,
    ledger: TrialLedger | None = None,
    ledger_path: Path | None = None,
    train_fraction: float = 0.70,
    embargo_bars: int = 2,
    venue: str = "binance",
    market_type: str = "spot",
    periods_per_year: float | None = None,
    scan_id: str | None = None,
    opportunity_id: str | None = None,
) -> ValidateCandidateResult:
    """Una candidata × una estrategia × una config. Siempre registra el trial."""
    from quantlab.research.alpha.opportunity import (
        effective_embargo_bars,
        make_opportunity_id,
        periods_per_year_for_timeframe,
        ranking_b_status,
    )
    from quantlab.workbench.lab_services import run_lab_backtest
    from quantlab.workbench.strategy_catalog import normalize_strategy_id

    sid = normalize_strategy_id(strategy_id)
    ph = _params_hash(params)
    led = ledger or TrialLedger(path=ledger_path)
    pipe = ValidationPipeline(ledger=led)
    trial_id = f"val_{uuid4().hex[:12]}"
    opp = opportunity_id or make_opportunity_id(
        signal=signal, scan_id=scan_id, venue=venue, market_type=market_type
    )
    ppy = (
        periods_per_year
        if periods_per_year is not None
        else periods_per_year_for_timeframe(signal.timeframe)
    )
    n_for_embargo = 0
    if bars is not None:
        n_for_embargo = len(bars)
    elif bars_a is not None and bars_b is not None:
        n_for_embargo = min(len(bars_a), len(bars_b))
    embargo = effective_embargo_bars(
        requested=embargo_bars,
        lookback=signal.lookback,
        n_bars=n_for_embargo,
        train_fraction=train_fraction,
    )
    pair_engine: str | None = None

    def _feed() -> dict[str, Any] | None:
        from quantlab.research.alpha.ml.feed import maybe_feed_ml

        path = ledger_path if ledger_path is not None else led.path
        return maybe_feed_ml(ledger_path=path)

    def _base_meta() -> dict[str, Any]:
        return {
            "phase": "validation",
            "strategy_id": sid,
            "params_hash": ph,
            "signal_id": signal.signal_id,
            "opportunity_id": opp,
            "scan_id": scan_id,
            "scope": signal.scope.value,
            "selection_raw_score": signal.raw_score,
            "selection_normalized_score": signal.normalized_score,
            "confidence": signal.confidence,
            "timeframe": signal.timeframe,
            "market_type": market_type,
            "venue": venue,
        }

    def _log(meta: dict[str, Any]) -> int:
        led.log(
            trial_id=trial_id,
            detector_id="validate_candidate",
            signal_type=signal.signal_type,
            symbols=signal.symbols,
            lag=signal.lag,
            lookback=signal.lookback,
            metadata=meta,
        )
        return led.count()

    def _result(
        *,
        ev: BacktestEvalResult,
        ok: bool,
        error: str | None,
        n: int,
        validated: bool,
    ) -> ValidateCandidateResult:
        return ValidateCandidateResult(
            eval=ev,
            strategy_id=sid,
            params_hash=ph,
            scope=signal.scope.value,
            symbols=signal.symbols,
            ok=ok,
            error=error,
            n_trials_at_eval=n,
            ml_feed=_feed(),
            trial_id=trial_id,
            opportunity_id=opp,
            scan_id=scan_id,
            status=ranking_b_status(validated=validated, ok=ok),
            pair_engine=pair_engine,
        )

    try:
        if signal.scope is SignalScope.PAIR or len(signal.symbols) == 2:
            pair_engine = "spread_oos_train_beta"
            net = _pair_net_returns(
                bars_a=bars_a,
                bars_b=bars_b,
                train_fraction=train_fraction,
                embargo_bars=embargo,
                venue=venue,
                market_type=market_type,
            )
        else:
            if bars is None or len(bars) < 16:
                raise ValidationError("validate_candidate individual requiere ≥16 barras")
            train, test = split_bars_train_test(
                list(bars),
                train_fraction=train_fraction,
                embargo_bars=embargo,
            )
            if len(test) < 4:
                raise ValidationError("tramo test insuficiente tras embargo")
            _ = train
            bt = run_lab_backtest(
                strategy_id=sid,
                params=dict(params or {}),
                bars=list(test),
                instrument_id=signal.symbols[0] if signal.symbols else None,
                data_source="validate_candidate_oos",
                experiment_id=f"val-{trial_id}"[:120],
                initial_cash=Decimal("100000"),
            )
            net = _returns_from_backtest_payload(bt)
            if not net:
                try:
                    ini = float(bt.get("initial_equity") or 0)
                    fin = float(bt.get("final_equity") or 0)
                    if ini > 0:
                        net = ((fin - ini) / ini,)
                except (TypeError, ValueError):
                    net = ()

        if not net:
            n = _log(
                {
                    **_base_meta(),
                    "ok": False,
                    "error": "sin retornos netos",
                    "validated": False,
                }
            )
            return _result(
                ev=_empty_eval(signal.signal_id),
                ok=False,
                error="sin retornos netos",
                n=n,
                validated=False,
            )

        ev = pipe.evaluate_backtest(signal, net_returns=net, periods_per_year=ppy)
        n = _log(
            {
                **_base_meta(),
                "ok": True,
                "error": None,
                "sharpe_net": ev.sharpe_net,
                "deflated_sharpe": ev.deflated_sharpe,
                "max_drawdown": ev.max_drawdown,
                "validated": ev.validated,
                "status": ranking_b_status(validated=ev.validated, ok=True),
                "pair_engine": pair_engine,
                "embargo_bars": embargo,
                "periods_per_year": ppy,
            }
        )
        return _result(ev=ev, ok=True, error=None, n=n, validated=ev.validated)
    except (ValidationError, ValueError, TypeError, KeyError) as exc:
        n = _log({**_base_meta(), "ok": False, "error": str(exc), "validated": False})
        return _result(
            ev=_empty_eval(signal.signal_id),
            ok=False,
            error=str(exc),
            n=n,
            validated=False,
        )


def _pair_net_returns(
    *,
    bars_a: Sequence[Bar] | None,
    bars_b: Sequence[Bar] | None,
    train_fraction: float,
    embargo_bars: int,
    venue: str,
    market_type: str,
) -> tuple[float, ...]:
    from quantlab.backtester.pair_engine import run_spread_backtest
    from quantlab.research.alpha.pairwise.align import align_pair_bars
    from quantlab.research.alpha.pairwise.costs import estimate_pair_cost_bps
    from quantlab.research.alpha.pairwise.stats import ols_hedge_ratio

    if bars_a is None or bars_b is None:
        raise ValidationError("validate_candidate pair requiere bars_a y bars_b")
    aligned = align_pair_bars(list(bars_a), list(bars_b))
    if aligned is None:
        raise ValidationError("pares no alineables")
    n = len(aligned.closes_a)
    cut = int(n * train_fraction)
    cut = max(1, min(cut, n - 1))
    start = cut + max(0, embargo_bars)
    if start >= n - 5:
        raise ValidationError("tramo OOS par insuficiente")
    train_a = aligned.closes_a[:cut]
    train_b = aligned.closes_b[:cut]
    if len(train_a) < 8:
        raise ValidationError("tramo train par insuficiente para hedge ratio")
    beta = ols_hedge_ratio(list(train_a), list(train_b))
    test_a = aligned.closes_a[start:]
    test_b = aligned.closes_b[start:]
    z_window = min(48, max(10, len(test_a) // 3))
    fee = estimate_pair_cost_bps(venue=venue, market_type=market_type) / 2.0
    bt = run_spread_backtest(
        test_a,
        test_b,
        fee_bps_per_leg=fee,
        hedge_ratio=beta,
        z_window=z_window,
    )
    return bt.net_returns


def list_ranking_b_from_ledger(ledger: TrialLedger) -> list[dict[str, Any]]:
    """Ranking B: todas las validaciones (aprobadas, rechazadas, fallidas)."""
    from quantlab.research.alpha.opportunity import ranking_b_status

    rows: list[dict[str, Any]] = []
    for rec in ledger.records():
        meta = rec.metadata or {}
        if meta.get("phase") != "validation":
            continue
        validated = meta.get("validated") is True
        ok = meta.get("ok") is not False
        status = str(meta.get("status") or ranking_b_status(validated=validated, ok=ok))
        rows.append(
            {
                "trial_id": rec.trial_id,
                "opportunity_id": meta.get("opportunity_id"),
                "scan_id": meta.get("scan_id"),
                "signal_id": meta.get("signal_id"),
                "strategy_id": meta.get("strategy_id"),
                "symbols": list(rec.symbols),
                "signal_type": rec.signal_type,
                "sharpe_net": meta.get("sharpe_net"),
                "deflated_sharpe": meta.get("deflated_sharpe"),
                "max_drawdown": meta.get("max_drawdown"),
                "params_hash": meta.get("params_hash"),
                "created_at": rec.created_at,
                "validated": validated,
                "ok": ok,
                "status": status,
                "error": meta.get("error"),
            }
        )
    rows.sort(
        key=lambda r: (
            0 if r.get("status") == "validated_historically" else 1,
            -float(r.get("deflated_sharpe") or 0.0),
        )
    )
    return rows


def list_validated_from_ledger(ledger: TrialLedger) -> list[dict[str, Any]]:
    """Subset Ranking B: solo validated=True (compat)."""
    return [r for r in list_ranking_b_from_ledger(ledger) if r.get("validated") is True]


__all__ = [
    "ValidateCandidateResult",
    "default_trials_path",
    "equity_curve_to_returns",
    "list_ranking_b_from_ledger",
    "list_validated_from_ledger",
    "validate_candidate",
]
