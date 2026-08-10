"""Orquestación de ejecución estrategia: paper + preflight testnet (sin órdenes remotas MVP)."""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quantlab.brokers.binance.demo_transport import demo_transport_status
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.execution.strategy_execution.destinations import (
    MAX_ACTIVE_STRATEGIES,
    ExecutionDestination,
    ExecutionSessionState,
    MarketDataSource,
)
from quantlab.execution.strategy_execution.hummingbot_manager import get_hummingbot_manager
from quantlab.execution.strategy_execution.manifest import (
    StrategyPromotionManifest,
    build_manifest_from_body,
)
from quantlab.execution.strategy_execution.registry import get_registry
from quantlab.execution.strategy_execution.store import (
    ExecutionSessionRecord,
    ExecutionStore,
    now_iso,
)


@dataclass
class PreflightResult:
    ok: bool
    checks: list[dict[str, Any]]
    ready_for_spot_testnet_order: bool
    ready_for_futures_testnet_order: bool
    blockers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": self.checks,
            "ready_for_spot_testnet_order": self.ready_for_spot_testnet_order,
            "ready_for_futures_testnet_order": self.ready_for_futures_testnet_order,
            "blockers": self.blockers,
            "production_blocked": LIVE_BLOCKED is True,
            "remote_orders_enabled": False,
        }


class StrategyExecutionService:
    def __init__(self, store: ExecutionStore) -> None:
        self.store = store
        self.registry = get_registry()
        self.hb = get_hummingbot_manager()

    def list_strategies(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.registry.list_strategies()]

    def get_strategy_capabilities(self, strategy_id: str) -> dict[str, Any]:
        return self.registry.get(strategy_id).to_dict()

    def create_promotion(self, body: Mapping[str, Any]) -> StrategyPromotionManifest:
        payload = dict(body)
        if payload.get("strategy_id"):
            caps = self.registry.get(str(payload["strategy_id"]))
            if not payload.get("strategy_name"):
                payload["strategy_name"] = caps.strategy_name
            if not payload.get("strategy_parameters"):
                payload["strategy_parameters"] = dict(caps.default_parameters)
        manifest = build_manifest_from_body(payload)
        self.store.save_promotion(manifest)
        return manifest

    def get_promotion(self, promotion_id: str) -> StrategyPromotionManifest:
        return self.store.load_promotion(promotion_id)

    def validate_promotion(self, promotion_id: str) -> dict[str, Any]:
        manifest = self.get_promotion(promotion_id)
        caps = self.registry.get(manifest.strategy_id)
        errors: list[str] = []
        dest = manifest.execution_destination
        if dest == ExecutionDestination.PAPER and not caps.paper_supported:
            errors.append(f"{manifest.strategy_id} no soporta PAPER")
        if dest == ExecutionDestination.BINANCE_SPOT_TESTNET and not caps.spot_testnet_supported:
            errors.append(f"{manifest.strategy_id} no certificada para Spot Testnet")
        if (
            dest == ExecutionDestination.BINANCE_FUTURES_TESTNET
            and not caps.futures_testnet_supported
        ):
            errors.append(f"{manifest.strategy_id} no certificada para Futures Testnet")
        return {
            "ok": not errors,
            "errors": errors,
            "manifest": manifest.to_dict(),
            "capabilities": caps.to_dict(),
        }

    def preflight(self, promotion_id: str, *, unlocked: bool) -> PreflightResult:
        manifest = self.get_promotion(promotion_id)
        val = self.validate_promotion(promotion_id)
        checks: list[dict[str, Any]] = []
        blockers: list[str] = list(val.get("errors") or [])

        checks.append({"name": "production_blocked", "ok": LIVE_BLOCKED is True})
        if not LIVE_BLOCKED:
            blockers.append("LIVE_BLOCKED=False")

        checks.append({"name": "manifest_valid", "ok": val["ok"]})
        checks.append({"name": "testnet_only", "ok": manifest.testnet_only})
        paper_dest = manifest.execution_destination == ExecutionDestination.PAPER
        checks.append({"name": "live_unlock", "ok": unlocked or paper_dest})
        if manifest.execution_destination != ExecutionDestination.PAPER and not unlocked:
            blockers.append("Requiere unlock LIVE local")

        active = self.store.find_active_session()
        checks.append({"name": "single_active_strategy", "ok": active is None})
        if active is not None:
            blockers.append(f"Sesión activa: {active.session_id}")

        demo = demo_transport_status(unlocked=unlocked)
        checks.append({"name": "demo_transport", "ok": True, "detail": demo})

        dest = manifest.execution_destination
        if dest == ExecutionDestination.BINANCE_SPOT_TESTNET:
            tn = demo.get("testnet") or {}
            keys_ok = bool(tn.get("keys_configured")) and bool(tn.get("remote_enabled"))
            checks.append({"name": "spot_testnet_keys", "ok": keys_ok})
            if not keys_ok:
                blockers.append("Spot Testnet: keys o flag ausente")
        if dest == ExecutionDestination.BINANCE_FUTURES_TESTNET:
            fn = demo.get("futures_testnet") or {}
            keys_ok = bool(fn.get("keys_configured")) and bool(fn.get("remote_enabled"))
            hb_pf = self.hb.preflight_for_futures()
            checks.append({"name": "futures_testnet_keys", "ok": keys_ok})
            checks.append(
                {
                    "name": "hummingbot_futures",
                    "ok": hb_pf.get("ready_for_strategy_load"),
                    "detail": hb_pf,
                }
            )
            if not keys_ok:
                blockers.append("Futures Testnet: keys o flag ausente")
            if not hb_pf.get("ready_for_strategy_load"):
                blockers.append("Hummingbot no listo para Futures")

        ok = not blockers and all(
            c.get("ok") is not False for c in checks if c.get("ok") is not None
        )
        # MVP: nunca autorizar órdenes remotas automáticamente
        return PreflightResult(
            ok=ok,
            checks=checks,
            ready_for_spot_testnet_order=False,
            ready_for_futures_testnet_order=False,
            blockers=blockers,
        )

    def open_session(self, promotion_id: str) -> ExecutionSessionRecord:
        manifest = self.get_promotion(promotion_id)
        active = self.store.find_active_session()
        if active is not None:
            raise ValidationError(
                f"MAX_ACTIVE_STRATEGIES={MAX_ACTIVE_STRATEGIES}: cierre {active.session_id} primero"
            )
        ts = now_iso()
        rec = ExecutionSessionRecord(
            session_id=uuid.uuid4().hex[:16],
            promotion_id=promotion_id,
            state=ExecutionSessionState.DRAFT,
            created_at=ts,
            updated_at=ts,
            manifest=manifest,
        )
        rec.events.append({"at": ts, "kind": "session_opened", "promotion_id": promotion_id})
        self.store.save_session(rec)
        return rec

    def get_session(self, session_id: str) -> ExecutionSessionRecord:
        return self.store.load_session(session_id)

    def session_status(self, session_id: str) -> dict[str, Any]:
        rec = self.get_session(session_id)
        caps = self.registry.get(rec.manifest.strategy_id)
        dest = rec.manifest.execution_destination
        funds = "SIMULADOS" if dest == ExecutionDestination.PAPER else "DE PRUEBA"
        return {
            "session": rec.to_dict(),
            "capabilities": caps.to_dict(),
            "security_banner": {
                "market_data": "REALES",
                "orders": dest.value,
                "funds": funds,
                "production": "BLOQUEADA",
            },
            "max_active_strategies": MAX_ACTIVE_STRATEGIES,
        }

    def mark_validated(self, session_id: str) -> ExecutionSessionRecord:
        rec = self.get_session(session_id)
        rec.state = ExecutionSessionState.VALIDATED
        rec.updated_at = now_iso()
        rec.events.append({"at": rec.updated_at, "kind": "validated"})
        self.store.save_session(rec)
        return rec

    def mark_preflight_ok(self, session_id: str) -> ExecutionSessionRecord:
        rec = self.get_session(session_id)
        rec.state = ExecutionSessionState.PREFLIGHT_OK
        rec.updated_at = now_iso()
        rec.events.append({"at": rec.updated_at, "kind": "preflight_ok"})
        self.store.save_session(rec)
        return rec

    def stop_session(self, session_id: str) -> ExecutionSessionRecord:
        rec = self.get_session(session_id)
        rec.state = ExecutionSessionState.STOPPED
        rec.paper_session_running = False
        rec.updated_at = now_iso()
        rec.events.append({"at": rec.updated_at, "kind": "stopped"})
        self.store.save_session(rec)
        return rec

    def mark_paper_running(self, session_id: str) -> ExecutionSessionRecord:
        rec = self.get_session(session_id)
        rec.state = ExecutionSessionState.RUNNING
        rec.paper_session_running = True
        rec.updated_at = now_iso()
        rec.events.append({"at": rec.updated_at, "kind": "paper_started"})
        self.store.save_session(rec)
        return rec

    def list_sessions(self) -> list[ExecutionSessionRecord]:
        return self.store.list_sessions()


def default_store(session_root: str) -> ExecutionStore:
    return ExecutionStore(__import__("pathlib").Path(session_root) / "execution")


def build_manifest_from_scanner_prefill(body: Mapping[str, Any]) -> dict[str, Any]:
    """Helper promotion desde Alpha Scanner."""
    symbol = str(body.get("underlying") or body.get("symbol") or "BTCUSDT").upper()
    if not symbol.endswith("USDT") and len(symbol) <= 6:
        symbol = symbol + "USDT"
    dest = body.get("execution_destination") or ExecutionDestination.PAPER.value
    params = dict(body.get("strategy_parameters") or {})
    if not params:
        from quantlab.workbench.strategy_catalog import get_strategy_meta

        sid = str(body.get("strategy_id") or "buy_once")
        with contextlib.suppress(KeyError):
            params = dict(get_strategy_meta(sid).default_params)
    return {
        "source_module": "alpha_scanner",
        "scan_id": body.get("scan_id"),
        "strategy_id": body.get("strategy_id") or "buy_once",
        "strategy_name": body.get("strategy_id") or "buy_once",
        "strategy_parameters": params,
        "symbol": symbol,
        "market_type": body.get("market_type") or "spot",
        "execution_destination": dest,
        "market_data_source": MarketDataSource.BINANCE_PUBLIC_MD.value,
        "historical_metrics": {
            "score": body.get("score"),
            "profile": body.get("profile"),
            "interval": body.get("interval"),
            "venue": body.get("venue"),
            "underlying": body.get("underlying"),
            "strategies": body.get("strategies"),
        },
    }


def build_manifest_from_sim_context(body: Mapping[str, Any]) -> dict[str, Any]:
    ctx = body.get("sim_context") or body
    pairs = ctx.get("pairs") or []
    underlying = ctx.get("coin") or ctx.get("underlying")
    if not underlying and pairs:
        p0 = pairs[0]
        underlying = p0.get("ticker") or p0.get("underlying")
    venue = str(
        body.get("venue") or (ctx.get("venues") or ["binance"])[0] or "binance"
    ).lower()
    market_type = str(body.get("market_type") or ctx.get("market_type") or "spot").lower()
    symbol = str(body.get("symbol") or underlying or "BTC").upper()
    from quantlab.research.sim.symbol_map import resolve_instrument

    if underlying or symbol:
        with contextlib.suppress(ValidationError):
            resolved = resolve_instrument(
                str(underlying or symbol),
                venue=venue,
                market_type=market_type,
            )
            symbol = resolved.symbol.upper().replace("-", "").replace("/", "")
    elif not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    dest = body.get("execution_destination") or ExecutionDestination.PAPER.value
    cap = body.get("capital") or ctx.get("initial_capital") or ctx.get("capital")
    lev = body.get("leverage") or ctx.get("leverage")
    sid = ctx.get("strategy_id") or body.get("strategy_id") or "buy_once"
    params = dict(body.get("strategy_parameters") or ctx.get("params") or {})
    if not params:
        from quantlab.workbench.strategy_catalog import get_strategy_meta

        with contextlib.suppress(KeyError):
            params = dict(get_strategy_meta(str(sid)).default_params)
    return {
        "source_module": str(body.get("source_module") or "simulator"),
        "simulation_id": body.get("simulation_id"),
        "scan_id": body.get("scan_id") or ctx.get("scan_id"),
        "strategy_id": sid,
        "strategy_parameters": params,
        "symbol": symbol,
        "market_type": body.get("market_type") or ctx.get("market_type") or "spot",
        "execution_destination": dest,
        "market_data_source": MarketDataSource.BINANCE_PUBLIC_MD.value,
        "capital": str(cap) if cap is not None else None,
        "leverage": str(lev) if lev is not None else None,
        "historical_metrics": {
            "summary_line": ctx.get("summary_line"),
            "interval": ctx.get("interval") or body.get("interval"),
            "period_days": ctx.get("period_days") or body.get("period_days"),
            "venues": ctx.get("venues"),
            "venue": body.get("venue") or (ctx.get("venues") or [None])[0],
            "pairs": pairs,
            "leverage": lev,
            "per_trade_usd": ctx.get("per_trade_usd") or body.get("per_trade_usd"),
            "market_type": ctx.get("market_type") or body.get("market_type"),
            "strategy_label": ctx.get("strategy_label"),
            "interval_ms": body.get("interval_ms"),
        },
    }


def build_manifest_from_montecarlo_context(body: Mapping[str, Any]) -> dict[str, Any]:
    """Helper promotion desde Monte Carlo (hereda sim_context + métricas MC)."""
    base = build_manifest_from_sim_context(body)
    base["source_module"] = "montecarlo"
    mc_id = body.get("monte_carlo_id")
    if mc_id:
        base["monte_carlo_id"] = mc_id
    mc_metrics = dict(body.get("monte_carlo_metrics") or {})
    if mc_metrics:
        base["monte_carlo_metrics"] = mc_metrics
    hist = dict(base.get("historical_metrics") or {})
    if body.get("backtest_id"):
        hist["backtest_id"] = body.get("backtest_id")
    if body.get("scan_id"):
        base["scan_id"] = body.get("scan_id")
        hist["scan_id"] = body.get("scan_id")
    if mc_metrics:
        hist["monte_carlo"] = mc_metrics
    base["historical_metrics"] = hist
    return base
