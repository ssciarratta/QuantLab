"""API Workbench — ejecución estrategia (paper + preflight testnet)."""

from __future__ import annotations

import contextlib
from typing import Any

from quantlab.brokers.paper.broker import PaperBroker
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.execution.strategy_execution import (
    StrategyExecutionService,
    build_manifest_from_montecarlo_context,
    build_manifest_from_scanner_prefill,
    build_manifest_from_sim_context,
    default_store,
)
from quantlab.execution.strategy_execution.destinations import (
    ExecutionDestination,
    ExecutionSessionState,
)
from quantlab.execution.strategy_execution.registry import is_paper_run_certified
from quantlab.workbench.api import (
    ApiError,
    WorkbenchState,
    handle_get_instruments,
    handle_get_paper_book,
    handle_get_paper_equity,
    handle_get_paper_fills,
    handle_get_paper_pnl,
    handle_get_paper_session_status,
    handle_get_positions,
    handle_get_snapshot,
    handle_post_broker_connect,
    handle_post_paper_session_start,
    handle_post_paper_session_step,
    handle_post_paper_session_stop,
)


def _svc(state: WorkbenchState) -> StrategyExecutionService:
    session = state.ensure_session()
    return StrategyExecutionService(default_store(str(session.root)))


def _promotion_payload(body: dict[str, Any]) -> dict[str, Any]:
    if body.get("source_module") == "alpha_scanner":
        return dict(build_manifest_from_scanner_prefill(body))
    if body.get("source_module") == "montecarlo":
        return dict(build_manifest_from_montecarlo_context(body))
    if body.get("source_module") == "simulator" or body.get("sim_context"):
        return dict(build_manifest_from_sim_context(body))
    return dict(body)


def _resolve_broker_symbol(
    state: WorkbenchState,
    manifest_symbol: str,
    *,
    venue: str | None = None,
    market_type: str | None = None,
    underlying: str | None = None,
) -> str:
    """Resuelve símbolo broker; nunca sustituye silenciosamente por BTC/ETH."""
    from quantlab.research.sim.symbol_map import resolve_instrument

    raw = (underlying or manifest_symbol or "").strip()
    v = (venue or "binance").strip().lower()
    mt = (market_type or "spot").strip().lower()
    want = manifest_symbol.upper().replace("/", "")
    if raw:
        with contextlib.suppress(ValidationError):
            resolved = resolve_instrument(raw, venue=v, market_type=mt)
            want = resolved.symbol.upper().replace("-", "").replace("/", "")
    if not isinstance(state.broker, PaperBroker):
        return want
    instruments = handle_get_instruments(state).get("instruments") or []
    for inst in instruments:
        sym = str(inst.get("symbol") or "")
        if sym.upper() == want:
            return sym
    return want


def _manifest_underlying(manifest: Any) -> str | None:
    hist = getattr(manifest, "historical_metrics", None) or {}
    if not isinstance(hist, dict):
        hist = {}
    pairs = hist.get("pairs") or []
    if pairs and isinstance(pairs[0], dict):
        p0 = pairs[0]
        return str(p0.get("ticker") or p0.get("underlying") or "") or None
    sym = str(getattr(manifest, "symbol", "") or "")
    if sym.upper().endswith("USDT"):
        return sym[: -len("USDT")]
    return sym or None


def _ensure_paper_broker(state: WorkbenchState) -> None:
    if isinstance(state.broker, PaperBroker):
        return
    handle_post_broker_connect(state, {"venue": "binance", "mode": "paper"})


def _market_snapshot(
    state: WorkbenchState,
    symbol: str | None,
    manifest: Any | None = None,
) -> dict[str, Any] | None:
    if not symbol or not isinstance(state.broker, PaperBroker):
        return None
    hist: dict[str, Any] = {}
    mt = "spot"
    venue = state.venue or "binance"
    underlying: str | None = None
    if manifest is not None:
        hist = getattr(manifest, "historical_metrics", None) or {}
        if not isinstance(hist, dict):
            hist = {}
        mt = str(getattr(manifest, "market_type", None) or hist.get("market_type") or "spot")
        venue = str(hist.get("venue") or (hist.get("venues") or [venue])[0] or venue)
        underlying = _manifest_underlying(manifest)
    resolved = _resolve_broker_symbol(
        state, symbol, venue=venue, market_type=mt, underlying=underlying
    )
    with contextlib.suppress(ApiError, ValidationError, OSError, ValueError):
        out = handle_get_snapshot(state, f"symbol={resolved}")
        return out.get("snapshot")
    return None


def _safe_positions(state: WorkbenchState) -> list[dict[str, Any]]:
    with contextlib.suppress(ApiError):
        return list(handle_get_positions(state).get("positions") or [])
    return []


def _enriched_live(state: WorkbenchState, session_id: str | None = None) -> dict[str, Any]:
    svc = _svc(state)
    rec = None
    if session_id:
        with contextlib.suppress(FileNotFoundError):
            rec = svc.get_session(session_id)
    if rec is None:
        rec = svc.store.find_active_session()
    fills_payload = handle_get_paper_fills(state)
    fills = list(fills_payload.get("fills") or [])
    equity_payload = handle_get_paper_equity(state, "limit=80")
    out: dict[str, Any] = {
        "paper_status": handle_get_paper_session_status(state),
        "pnl": handle_get_paper_pnl(state),
        "equity_curve": list(equity_payload.get("points") or []),
        "fills": fills[-50:],
        "fills_count": len(fills),
        "book": handle_get_paper_book(state),
        "positions": _safe_positions(state),
        "broker_connected": isinstance(state.broker, PaperBroker),
        "venue": state.venue,
    }
    if rec is not None:
        manifest = rec.manifest
        out["execution_session"] = rec.to_dict()
        out["market"] = _market_snapshot(state, manifest.symbol, manifest)
        out["capabilities"] = svc.get_strategy_capabilities(manifest.strategy_id)
        out["last_fill"] = fills[-1] if fills else None
        ps = out["paper_status"]
        running = bool(rec.paper_session_running and ps.get("running"))
        steps = int(ps.get("steps") or 0)
        max_steps = int(ps.get("max_steps") or 0)
        hist = manifest.historical_metrics or {}
        sym_resolved = _resolve_broker_symbol(
            state,
            manifest.symbol,
            venue=str(
                hist.get("venue")
                or (hist.get("venues") or [None])[0]
                or state.venue
                or "binance"
            ),
            market_type=str(manifest.market_type or hist.get("market_type") or "spot"),
            underlying=_manifest_underlying(manifest),
        )
        paper_blocker: str | None = None
        if not running and manifest.execution_destination == ExecutionDestination.PAPER:
            if not is_paper_run_certified(manifest.strategy_id):
                paper_blocker = (
                    f"{manifest.strategy_id} no ejecutable en paper (solo stubs research)"
                )
            elif not rec.paper_session_running and steps <= 0:
                paper_blocker = "Sesión registrada; corrida paper no iniciada"
        out["live_summary"] = {
            "phase": "RUNNING" if running else rec.state.value,
            "strategy_id": manifest.strategy_id,
            "strategy_name": manifest.strategy_name,
            "symbol": manifest.symbol,
            "symbol_resolved": sym_resolved
            if isinstance(state.broker, PaperBroker)
            else manifest.symbol,
            "destination": manifest.execution_destination.value,
            "steps": steps,
            "max_steps": max_steps,
            "progress_pct": round(100 * steps / max_steps, 1) if max_steps else 0,
            "paper_running": running,
            "paper_blocker": paper_blocker,
            "error": ps.get("last_error") or rec.error,
            "session_id": rec.session_id,
            "promotion_id": manifest.promotion_id,
        }
    return out


def _build_closure_summary(
    live: dict[str, Any],
    *,
    reason: str,
    stages: list[dict[str, Any]] | None = None,
    paper_started: bool | None = None,
    paper_blocker: str | None = None,
) -> dict[str, Any]:
    """Resumen legible: qué se hizo y qué no al cerrar una corrida."""
    summary = live.get("live_summary") or {}
    sess = live.get("execution_session") or {}
    manifest = sess.get("manifest") or {}
    ps = live.get("paper_status") or {}
    pnl = live.get("pnl") or {}
    caps = live.get("capabilities") or {}

    stage_labels = {
        "promotion": "Promoción creada",
        "validate": "Validación de manifiesto",
        "preflight": "Preflight de seguridad",
        "open_session": "Sesión de ejecución registrada",
        "start_paper": "Motor paper en vivo (fills)",
        "start_testnet_engine": "Motor paper + espejo testnet",
        "release_previous_session": "Sesión anterior cerrada",
    }

    done: list[str] = []
    not_done: list[str] = []

    if stages:
        for st in stages:
            label = stage_labels.get(str(st.get("name")), str(st.get("name")))
            detail = st.get("detail")
            if st.get("ok"):
                done.append(f"{label}" + (f" · {detail}" if detail else ""))
            else:
                not_done.append(f"{label}: {detail or 'no completado'}")
    else:
        if sess.get("session_id"):
            done.append(f"Sesión {sess.get('session_id')} · estado {sess.get('state', '?')}")
        if manifest.get("promotion_id"):
            done.append(f"Promoción {manifest.get('promotion_id')}")

    if paper_started is True:
        steps = int(ps.get("steps") or summary.get("steps") or 0)
        max_s = int(ps.get("max_steps") or summary.get("max_steps") or 0)
        done.append(f"Corrida paper ejecutada · steps {steps}/{max_s or '?'}")
    elif paper_blocker:
        not_done.append(paper_blocker)
    elif paper_started is False:
        not_done.append("Motor paper no arrancó")

    fills = int(live.get("fills_count") or 0)
    if fills > 0:
        done.append(f"{fills} fill(s) en journal paper")
    elif paper_started:
        not_done.append("Sin fills registrados (estrategia no operó o corrida muy corta)")

    sid = manifest.get("strategy_id") or summary.get("strategy_id") or "?"
    if not caps.get("paper_run_certified") and sid != "?":
        not_done.append(f"Estrategia {sid} no runnable en catálogo paper")

    dest = str(manifest.get("execution_destination") or summary.get("destination") or "")
    mirror = ps.get("testnet_mirror") or {}
    mirror_mode = str(mirror.get("mode") or "none")
    if "TESTNET" in dest.upper():
        if mirror_mode in {"spot", "futures"}:
            ok_n = int(mirror.get("ok") or 0)
            att = int(mirror.get("attempts") or 0)
            if ok_n > 0:
                done.append(f"Espejo testnet {mirror_mode}: {ok_n} orden(es) real(es) enviada(s)")
            elif att > 0:
                not_done.append(
                    f"Espejo testnet {mirror_mode}: intentos={att} · sin órdenes "
                    "(unlock demo + flag/keys en .env)"
                )
            else:
                not_done.append(
                    f"Espejo testnet {mirror_mode}: omitido (unlock demo + flag/keys en .env)"
                )
        else:
            not_done.append("Espejo testnet no configurado para este destino")
    elif reason not in {"started"}:
        not_done.append("Órdenes en exchange real (solo testnet cuando está cableado)")

    if LIVE_BLOCKED and reason not in {"started"}:
        not_done.append("Producción LIVE (siempre bloqueada)")

    headlines = {
        "stopped": "Detenida manualmente — resumen final",
        "completed": "Corrida finalizada — resumen",
        "started": "Motor arrancado — seguí el progreso arriba",
        "registered_only": "Registro completado — sin motor paper",
        "error": "Corrida con errores — resumen",
    }
    headline = headlines.get(reason, "Resumen de ejecución")

    return {
        "outcome": reason,
        "headline": headline,
        "done": done,
        "not_done": not_done,
        "metrics": {
            "fills": fills,
            "steps": ps.get("steps") if ps.get("steps") is not None else summary.get("steps"),
            "max_steps": (
                ps.get("max_steps")
                if ps.get("max_steps") is not None
                else summary.get("max_steps")
            ),
            "equity": pnl.get("equity"),
            "realized_pnl": pnl.get("realized_pnl"),
            "unrealized_pnl": pnl.get("unrealized_pnl"),
            "cash": pnl.get("cash"),
            "session_state": sess.get("state") or summary.get("phase"),
            "strategy_id": sid,
            "strategy_name": manifest.get("strategy_name") or summary.get("strategy_name"),
            "symbol": summary.get("symbol_resolved") or manifest.get("symbol"),
            "destination": manifest.get("execution_destination") or summary.get("destination"),
            "error": summary.get("error") or ps.get("last_error"),
        },
    }


def handle_get_execution_strategies(state: WorkbenchState) -> dict[str, Any]:
    from quantlab.execution.strategy_execution.registry import get_registry
    from quantlab.workbench.strategy_guides import FAMILY_LABELS_ES

    _ = state  # sesión workbench no altera catálogo
    caps = get_registry().list_strategies()
    strategies = [c.to_dict() for c in caps]
    families = sorted({c.family for c in caps})
    runnable_count = sum(1 for s in strategies if s.get("paper_run_certified"))
    stub_count = len(strategies) - runnable_count
    return {
        "ok": True,
        "strategies": strategies,
        "catalog_stats": {
            "total": len(strategies),
            "runnable": runnable_count,
            "stub": stub_count,
        },
        "family_labels_es": {f: FAMILY_LABELS_ES.get(f, f) for f in families},
        "family_order": [
            "demo",
            "trend",
            "momentum",
            "mean_reversion",
            "market_making",
            "stats",
            "ml",
            "multi_asset",
            "microstructure",
            "arbitrage",
            "options",
        ],
        "production_blocked": LIVE_BLOCKED is True,
    }


def handle_get_execution_strategy_capabilities(
    state: WorkbenchState, strategy_id: str
) -> dict[str, Any]:
    svc = _svc(state)
    try:
        caps = svc.get_strategy_capabilities(strategy_id)
    except KeyError as exc:
        raise ApiError(404, str(exc)) from exc
    return {"ok": True, "capabilities": caps}


def handle_post_execution_promotions(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    svc = _svc(state)
    try:
        manifest = svc.create_promotion(_promotion_payload(body))
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    return {"ok": True, "promotion": manifest.to_dict()}


def handle_get_execution_promotion(state: WorkbenchState, promotion_id: str) -> dict[str, Any]:
    svc = _svc(state)
    try:
        manifest = svc.get_promotion(promotion_id)
    except FileNotFoundError as exc:
        raise ApiError(404, f"promotion no encontrada: {promotion_id}") from exc
    return {"ok": True, "promotion": manifest.to_dict()}


def handle_post_execution_promotion_validate(
    state: WorkbenchState, promotion_id: str
) -> dict[str, Any]:
    svc = _svc(state)
    try:
        result = svc.validate_promotion(promotion_id)
    except FileNotFoundError as exc:
        raise ApiError(404, str(exc)) from exc
    return {"ok": True, **result}


def handle_post_execution_promotion_preflight(
    state: WorkbenchState, promotion_id: str
) -> dict[str, Any]:
    svc = _svc(state)
    from quantlab.execution.live_unlock import is_live_session_unlocked

    unlocked = is_live_session_unlocked()
    try:
        result = svc.preflight(promotion_id, unlocked=unlocked)
    except FileNotFoundError as exc:
        raise ApiError(404, str(exc)) from exc
    return {"ok": True, "preflight": result.to_dict()}


def handle_post_execution_promotion_open_session(
    state: WorkbenchState, promotion_id: str
) -> dict[str, Any]:
    svc = _svc(state)
    try:
        rec = svc.open_session(promotion_id)
    except (FileNotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, FileNotFoundError) else 409
        raise ApiError(status, str(exc)) from exc
    return {"ok": True, "session": rec.to_dict()}


def handle_get_execution_sessions(state: WorkbenchState) -> dict[str, Any]:
    svc = _svc(state)
    rows = sorted(svc.list_sessions(), key=lambda r: r.updated_at, reverse=True)
    return {"ok": True, "sessions": [r.to_dict() for r in rows]}


def handle_get_execution_live(
    state: WorkbenchState, session_id: str | None = None
) -> dict[str, Any]:
    return {"ok": True, "live": _enriched_live(state, session_id)}


def handle_get_execution_session_status(state: WorkbenchState, session_id: str) -> dict[str, Any]:
    svc = _svc(state)
    try:
        status = svc.session_status(session_id)
    except FileNotFoundError as exc:
        raise ApiError(404, str(exc)) from exc
    status["live"] = _enriched_live(state, session_id)
    return {"ok": True, **status}


def _release_active_execution_session(
    state: WorkbenchState, svc: StrategyExecutionService
) -> str | None:
    """Cierra sesión activa previa para permitir nueva corrida (MAX_ACTIVE=1)."""
    active = svc.store.find_active_session()
    if active is None:
        return None
    if active.paper_session_running:
        with contextlib.suppress(ApiError):
            handle_post_paper_session_stop(state)
    svc.stop_session(active.session_id)
    return active.session_id


def _start_engine_for_session(
    state: WorkbenchState,
    svc: StrategyExecutionService,
    session_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Arranca motor paper (+ espejo testnet si destino Spot/Futures Testnet)."""
    from quantlab.execution.strategy_execution.testnet_bridge import mirror_mode_for_destination

    rec = svc.get_session(session_id)
    manifest = rec.manifest
    dest = manifest.execution_destination
    if dest not in (
        ExecutionDestination.PAPER,
        ExecutionDestination.BINANCE_SPOT_TESTNET,
        ExecutionDestination.BINANCE_FUTURES_TESTNET,
    ):
        raise ApiError(400, f"destino no soportado para motor: {dest.value}")
    if not is_paper_run_certified(manifest.strategy_id):
        raise ApiError(
            409,
            f"{manifest.strategy_id} no es ejecutable (stub research o desconocida)",
        )
    active = svc.store.find_active_session()
    if (
        active is not None
        and active.session_id != session_id
        and active.state == ExecutionSessionState.RUNNING
    ):
        raise ApiError(
            409,
            f"Hay otra sesión RUNNING ({active.session_id}); detenela primero",
        )
    _ensure_paper_broker(state)
    hist = manifest.historical_metrics or {}
    symbol = _resolve_broker_symbol(
        state,
        manifest.symbol,
        venue=str(
            hist.get("venue")
            or (hist.get("venues") or [None])[0]
            or state.venue
            or "binance"
        ),
        market_type=str(manifest.market_type or hist.get("market_type") or "spot"),
        underlying=_manifest_underlying(manifest),
    )
    max_steps = body.get("max_steps", 25)
    if not isinstance(max_steps, int) or isinstance(max_steps, bool):
        raise ApiError(400, "max_steps debe ser int")
    interval_ms = body.get("interval_ms", 800)
    if interval_ms is not None and not isinstance(interval_ms, int):
        raise ApiError(400, "interval_ms debe ser int o null")
    params = manifest.strategy_parameters or {}
    mirror = mirror_mode_for_destination(dest)
    paper_out = handle_post_paper_session_start(
        state,
        {
            "strategy_id": manifest.strategy_id,
            "symbol": symbol,
            "max_steps": max_steps,
            "interval_ms": interval_ms,
            "params": params,
            "testnet_mirror": mirror,
        },
    )
    with contextlib.suppress(ApiError):
        handle_post_paper_session_step(state)
    rec = svc.mark_paper_running(session_id)
    return {
        "session": rec.to_dict(),
        "paper": paper_out,
        "symbol_resolved": symbol,
        "testnet_mirror": mirror,
    }


def _start_paper_for_session(
    state: WorkbenchState,
    svc: StrategyExecutionService,
    session_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    rec = svc.get_session(session_id)
    if rec.manifest.execution_destination != ExecutionDestination.PAPER:
        raise ApiError(400, "start-paper solo aplica a destino PAPER")
    return _start_engine_for_session(state, svc, session_id, body)


def handle_post_execution_run(state: WorkbenchState, body: dict[str, Any]) -> dict[str, Any]:
    """Un click: promoción → validate → preflight → sesión → (paper si certificada)."""
    svc = _svc(state)
    stages: list[dict[str, Any]] = []

    def _stage(name: str, ok: bool, detail: Any = None) -> None:
        stages.append({"name": name, "ok": ok, "detail": detail})

    try:
        manifest = svc.create_promotion(_promotion_payload(body))
    except ValidationError as exc:
        raise ApiError(400, str(exc)) from exc
    _stage("promotion", True, manifest.promotion_id)

    val = svc.validate_promotion(manifest.promotion_id)
    _stage("validate", val["ok"], val.get("errors"))
    if not val["ok"]:
        raise ApiError(400, f"validate falló: {val.get('errors')}")

    released = _release_active_execution_session(state, svc)
    if released:
        _stage("release_previous_session", True, released)

    from quantlab.execution.live_unlock import is_live_session_unlocked

    pf = svc.preflight(manifest.promotion_id, unlocked=is_live_session_unlocked())
    _stage("preflight", pf.ok, {"blockers": pf.blockers, "warnings": pf.warnings})
    if not pf.ok:
        raise ApiError(400, f"preflight falló: {pf.blockers}")

    try:
        rec = svc.open_session(manifest.promotion_id)
    except ValidationError as exc:
        raise ApiError(409, str(exc)) from exc
    _stage("open_session", True, rec.session_id)

    paper_started = False
    paper_blocker: str | None = None
    testnet_mirror: str | None = None
    dest = rec.manifest.execution_destination
    if is_paper_run_certified(rec.manifest.strategy_id) and dest in (
        ExecutionDestination.PAPER,
        ExecutionDestination.BINANCE_SPOT_TESTNET,
        ExecutionDestination.BINANCE_FUTURES_TESTNET,
    ):
        out = _start_engine_for_session(state, svc, rec.session_id, body)
        paper_started = True
        testnet_mirror = out.get("testnet_mirror")
        stage_name = "start_paper"
        if dest != ExecutionDestination.PAPER:
            stage_name = "start_testnet_engine"
        _stage(stage_name, True, {"mirror": testnet_mirror, "destination": dest.value})
    else:
        if not is_paper_run_certified(rec.manifest.strategy_id):
            paper_blocker = (
                f"{rec.manifest.strategy_id} no ejecutable (stub research)"
            )
        else:
            paper_blocker = f"Destino no soportado: {dest.value}"
        _stage("start_paper", False, paper_blocker)

    live = _enriched_live(state, rec.session_id)
    ps = live.get("paper_status") or {}
    still_running = bool(paper_started and ps.get("running"))
    closure_reason = (
        "started"
        if still_running
        else ("completed" if paper_started else "registered_only")
    )
    closure: dict[str, Any] | None = None
    if not still_running:
        closure = _build_closure_summary(
            live,
            reason=closure_reason,
            stages=stages,
            paper_started=paper_started,
            paper_blocker=paper_blocker,
        )
    return {
        "ok": True,
        "promotion_id": manifest.promotion_id,
        "session_id": rec.session_id,
        "paper_started": paper_started,
        "paper_blocker": paper_blocker,
        "testnet_mirror": testnet_mirror,
        "preflight_warnings": pf.warnings,
        "stages": stages,
        "live": live,
        "session": live.get("execution_session"),
        "closure_summary": closure,
    }


def handle_post_execution_session_start_paper(
    state: WorkbenchState, session_id: str, body: dict[str, Any]
) -> dict[str, Any]:
    svc = _svc(state)
    try:
        out = _start_paper_for_session(state, svc, session_id, body)
    except FileNotFoundError as exc:
        raise ApiError(404, str(exc)) from exc
    live = _enriched_live(state, session_id)
    return {
        "ok": True,
        **out,
        "paper_status": live.get("paper_status"),
        "live": live,
    }


def handle_post_execution_session_stop(state: WorkbenchState, session_id: str) -> dict[str, Any]:
    svc = _svc(state)
    try:
        rec = svc.get_session(session_id)
    except FileNotFoundError as exc:
        raise ApiError(404, str(exc)) from exc
    paper_was_running = bool(rec.paper_session_running)
    stages: list[dict[str, Any]] = [
        {"name": "promotion", "ok": True, "detail": rec.manifest.promotion_id},
        {"name": "validate", "ok": True},
        {"name": "preflight", "ok": True},
        {"name": "open_session", "ok": True, "detail": rec.session_id},
    ]
    if paper_was_running:
        handle_post_paper_session_stop(state)
        stages.append({"name": "start_paper", "ok": True})
    elif not is_paper_run_certified(rec.manifest.strategy_id):
        stages.append(
            {
                "name": "start_paper",
                "ok": False,
                "detail": f"{rec.manifest.strategy_id} stub research",
            }
        )
    rec = svc.stop_session(session_id)
    live = _enriched_live(state, session_id)
    paper_blocker_val = None
    if not paper_was_running:
        paper_blocker_val = live.get("live_summary", {}).get("paper_blocker")
    closure = _build_closure_summary(
        live,
        reason="stopped",
        stages=stages,
        paper_started=paper_was_running,
        paper_blocker=paper_blocker_val,
    )
    return {
        "ok": True,
        "session": rec.to_dict(),
        "live": live,
        "closure_summary": closure,
    }


def handle_get_execution_hummingbot_status(state: WorkbenchState) -> dict[str, Any]:
    svc = _svc(state)
    return {"ok": True, "hummingbot": svc.hb.status()}
