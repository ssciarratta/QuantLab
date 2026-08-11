"""Diagnóstico integral Binance Spot Testnet — sin órdenes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from quantlab.brokers.binance.demo_transport import (
    demo_transport_status,
    remote_testnet_conflict,
    resolve_demo_transport,
)
from quantlab.brokers.binance.futures_testnet_client import (
    FUTURES_TESTNET_BASE_URL,
    BinanceFuturesTestnetClient,
    futures_testnet_keys_configured,
    public_futures_connectivity_check,
)
from quantlab.brokers.binance.testnet_client import (
    TESTNET_BASE_URL,
    BinanceTestnetClient,
    TestnetBalance,
    public_connectivity_check,
    testnet_keys_configured,
)
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.execution.live_unlock import live_unlock_status
from quantlab.execution_export.hummingbot_probe import hummingbot_status

_DEFAULT_SYMBOL = "BTCUSDT"
_DEFAULT_MIN_NOTIONAL_USDT = Decimal("10")
_DEFAULT_MIN_BASE_QTY = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class StrategyFundsCheck:
    symbol: str
    base_asset: str
    quote_asset: str
    has_quote_usdt: bool
    quote_free: str
    base_free: str
    min_notional_usdt: str
    sufficient_for_strategy: bool
    notes: tuple[str, ...]


def _decimal_positive(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return Decimal("0")
    if not parsed.is_finite() or parsed < 0:
        return Decimal("0")
    return parsed


def _split_symbol(symbol: str) -> tuple[str, str]:
    sym = symbol.strip().upper()
    if sym.endswith("USDT") and len(sym) > 4:
        return sym[:-4], "USDT"
    if sym.endswith("BUSD") and len(sym) > 4:
        return sym[:-4], "BUSD"
    raise ValidationError(f"símbolo no soportado para diagnóstico: {symbol!r}")


def _balance_map(balances: list[TestnetBalance]) -> dict[str, TestnetBalance]:
    return {b.asset: b for b in balances}


def assess_strategy_funds(
    balances: list[TestnetBalance],
    *,
    symbol: str = _DEFAULT_SYMBOL,
    min_notional_usdt: Decimal = _DEFAULT_MIN_NOTIONAL_USDT,
) -> StrategyFundsCheck:
    base_asset, quote_asset = _split_symbol(symbol)
    by_asset = _balance_map(balances)
    quote = by_asset.get(quote_asset)
    base = by_asset.get(base_asset)
    quote_free = quote.free if quote else "0"
    base_free = base.free if base else "0"
    quote_amount = _decimal_positive(quote_free)
    base_amount = _decimal_positive(base_free)
    has_quote = quote_amount >= min_notional_usdt
    has_base = base_amount >= _DEFAULT_MIN_BASE_QTY
    notes: list[str] = []
    if not has_quote:
        notes.append(
            f"Se requiere al menos {min_notional_usdt} {quote_asset} libre para órdenes BUY."
        )
    if not has_base:
        notes.append(
            f"Se requiere al menos {_DEFAULT_MIN_BASE_QTY} {base_asset} libre para órdenes SELL."
        )
    sufficient = has_quote or has_base
    if sufficient and not (has_quote and has_base):
        notes.append(
            "Fondos parciales: suficiente para una dirección (BUY o SELL), no para market making."
        )
    return StrategyFundsCheck(
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        has_quote_usdt=has_quote,
        quote_free=quote_free,
        base_free=base_free,
        min_notional_usdt=str(min_notional_usdt),
        sufficient_for_strategy=sufficient,
        notes=tuple(notes),
    )


def _quantlab_routing_status() -> dict[str, Any]:
    unlock = live_unlock_status()
    unlocked = bool(unlock.get("unlocked"))
    dt = demo_transport_status(unlocked=unlocked)
    transport = dt.get("transport")
    if transport is None:
        transport = "conflict" if dt.get("conflict") else "local_demo_sim"
    return {
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "unlock": unlock,
        "transport": transport,
        "testnet": dt.get("spot"),
        "futures_testnet": dt.get("futures"),
        "conflict": bool(dt.get("conflict")),
        "error": dt.get("error"),
        "note": dt.get("note"),
    }


def run_testnet_diagnostic(
    *,
    symbol: str = _DEFAULT_SYMBOL,
    skip_network: bool = False,
) -> dict[str, Any]:
    """Ejecuta diagnóstico completo sin crear órdenes."""
    issues: list[str] = []
    connectivity: dict[str, Any] | None = None
    auth: dict[str, Any] | None = None
    balances: list[dict[str, str]] = []
    strategy: dict[str, Any] | None = None
    hb = hummingbot_status()

    if not testnet_keys_configured():
        issues.append("Credenciales testnet ausentes (BINANCE_DEMO_API_KEY/SECRET).")
    flag = os.environ.get("QUANTLAB_DEMO_USE_TESTNET", "").strip().lower()
    if flag not in {"1", "true", "yes", "on"}:
        issues.append("QUANTLAB_DEMO_USE_TESTNET no está activo.")

    unlock = live_unlock_status()
    if not unlock.get("unlocked"):
        issues.append(
            "Unlock LIVE no activo (requerido para routing demo; "
            "diagnóstico de red sigue disponible)."
        )

    if LIVE_BLOCKED is not True:
        issues.append("CRÍTICO: LIVE_BLOCKED no es True.")

    # Safety: base URL must remain testnet
    if TESTNET_BASE_URL != "https://testnet.binance.vision":
        issues.append("CRÍTICO: TESTNET_BASE_URL inesperado.")

    client: BinanceTestnetClient | None = None
    if testnet_keys_configured():
        try:
            client = BinanceTestnetClient()
        except ValidationError as exc:
            issues.append(f"No se pudo instanciar cliente testnet: {exc}")

    if skip_network:
        connectivity = {"ok": None, "skipped": True, "note": "Red omitida (skip_network)."}
    elif client is not None:
        conn = client.connectivity_check()
        connectivity = {
            "ok": conn.ok,
            "ping_ok": conn.ping_ok,
            "server_time_ms": conn.server_time_ms,
            "base_url": conn.base_url,
            "error": conn.error,
        }
        if not conn.ok:
            issues.append(
                f"Conectividad testnet falló: {conn.error or 'ping/time inválido'}"
            )
    else:
        try:
            conn = public_connectivity_check()
            connectivity = {
                "ok": conn.ok,
                "ping_ok": conn.ping_ok,
                "server_time_ms": conn.server_time_ms,
                "base_url": conn.base_url,
                "error": conn.error,
                "auth_required_for_balances": True,
            }
            if not conn.ok:
                issues.append(
                    f"Conectividad pública testnet falló: {conn.error or 'ping/time inválido'}"
                )
        except ValidationError as exc:
            connectivity = {"ok": False, "error": str(exc)}
            issues.append(f"Conectividad testnet falló: {exc}")
        issues.append("Sin credenciales: balances y auth no disponibles.")

    if client is not None and not skip_network:
        auth_result = client.auth_check()
        auth = {
            "ok": auth_result.ok,
            "can_trade": auth_result.can_trade,
            "permissions": list(auth_result.permissions),
            "uid": auth_result.uid,
            "account_type": auth_result.account_type,
            "error": auth_result.error,
        }
        if not auth_result.ok:
            issues.append(f"Autenticación testnet falló: {auth_result.error}")
        elif not auth_result.can_trade:
            issues.append("Cuenta testnet reporta canTrade=false.")

        if auth_result.ok:
            try:
                parsed = client.get_balances(omit_zero=True)
                balances = [
                    {
                        "asset": b.asset,
                        "free": b.free,
                        "locked": b.locked,
                        "total": b.total,
                    }
                    for b in parsed
                ]
                if not balances:
                    issues.append("Cuenta testnet sin balances no-cero.")
                strat = assess_strategy_funds(parsed, symbol=symbol)
                strategy = {
                    "symbol": strat.symbol,
                    "base_asset": strat.base_asset,
                    "quote_asset": strat.quote_asset,
                    "has_quote_usdt": strat.has_quote_usdt,
                    "quote_free": strat.quote_free,
                    "base_free": strat.base_free,
                    "min_notional_usdt": strat.min_notional_usdt,
                    "sufficient_for_strategy": strat.sufficient_for_strategy,
                    "notes": list(strat.notes),
                }
                if not strat.sufficient_for_strategy:
                    issues.append(
                        "Fondos insuficientes para estrategia mínima en "
                        f"{symbol} (ver strategy.notes)."
                    )
            except ValidationError as exc:
                issues.append(f"No se pudieron leer balances: {exc}")

    if remote_testnet_conflict():
        issues.append(
            "Conflicto: Spot y Futures testnet remoto activos a la vez "
            "(desactive uno de los flags USE_*)."
        )

    routing = _quantlab_routing_status()
    if routing["transport"] != "binance_spot_testnet":
        issues.append(
            "QuantLab no está en transport binance_spot_testnet "
            f"(actual: {routing['transport']})."
        )

    ready = not issues and connectivity is not None and connectivity.get("ok") is True
    return {
        "market": "spot",
        "testnet_ready": ready,
        "base_url": TESTNET_BASE_URL,
        "production_blocked": True,
        "connectivity": connectivity,
        "auth": auth,
        "balances": balances,
        "strategy": strategy,
        "quantlab_routing": routing,
        "hummingbot": hb,
        "issues": issues,
    }


def run_futures_testnet_diagnostic(
    *,
    symbol: str = _DEFAULT_SYMBOL,
    skip_network: bool = False,
) -> dict[str, Any]:
    """Diagnóstico Futures USD-M Testnet sin crear órdenes."""
    issues: list[str] = []
    connectivity: dict[str, Any] | None = None
    auth: dict[str, Any] | None = None
    balances: list[dict[str, str]] = []
    strategy: dict[str, Any] | None = None
    hb = hummingbot_status()

    if not futures_testnet_keys_configured():
        issues.append(
            "Credenciales Futures testnet ausentes "
            "(BINANCE_FUTURES_DEMO_API_KEY/SECRET)."
        )
    flag = os.environ.get("QUANTLAB_DEMO_USE_FUTURES_TESTNET", "").strip().lower()
    if flag not in {"1", "true", "yes", "on"}:
        issues.append("QUANTLAB_DEMO_USE_FUTURES_TESTNET no está activo.")

    unlock = live_unlock_status()
    if not unlock.get("unlocked"):
        issues.append(
            "Unlock LIVE no activo (requerido para routing demo; "
            "diagnóstico de red sigue disponible)."
        )

    if LIVE_BLOCKED is not True:
        issues.append("CRÍTICO: LIVE_BLOCKED no es True.")

    if FUTURES_TESTNET_BASE_URL != "https://testnet.binancefuture.com":
        issues.append("CRÍTICO: FUTURES_TESTNET_BASE_URL inesperado.")

    if remote_testnet_conflict():
        issues.append(
            "Conflicto: Spot y Futures testnet remoto activos a la vez "
            "(desactive uno de los flags USE_*)."
        )

    client: BinanceFuturesTestnetClient | None = None
    if futures_testnet_keys_configured():
        try:
            client = BinanceFuturesTestnetClient()
        except ValidationError as exc:
            issues.append(f"No se pudo instanciar cliente futures testnet: {exc}")

    if skip_network:
        connectivity = {"ok": None, "skipped": True, "note": "Red omitida (skip_network)."}
    elif client is not None:
        conn = client.connectivity_check()
        connectivity = {
            "ok": conn.ok,
            "ping_ok": conn.ping_ok,
            "server_time_ms": conn.server_time_ms,
            "base_url": conn.base_url,
            "error": conn.error,
        }
        if not conn.ok:
            issues.append(
                f"Conectividad futures testnet falló: {conn.error or 'ping/time inválido'}"
            )
    else:
        try:
            conn = public_futures_connectivity_check()
            connectivity = {
                "ok": conn.ok,
                "ping_ok": conn.ping_ok,
                "server_time_ms": conn.server_time_ms,
                "base_url": conn.base_url,
                "error": conn.error,
                "auth_required_for_balances": True,
            }
            if not conn.ok:
                issues.append(
                    "Conectividad pública futures testnet falló: "
                    f"{conn.error or 'ping/time inválido'}"
                )
        except ValidationError as exc:
            connectivity = {"ok": False, "error": str(exc)}
            issues.append(f"Conectividad futures testnet falló: {exc}")
        issues.append("Sin credenciales Futures: balances y auth no disponibles.")

    if client is not None and not skip_network:
        auth_result = client.auth_check()
        auth = {
            "ok": auth_result.ok,
            "can_trade": auth_result.can_trade,
            "permissions": list(auth_result.permissions),
            "uid": auth_result.uid,
            "account_type": auth_result.account_type,
            "error": auth_result.error,
        }
        if not auth_result.ok:
            issues.append(f"Autenticación futures testnet falló: {auth_result.error}")
        elif not auth_result.can_trade:
            issues.append("Cuenta futures testnet reporta canTrade=false.")

        if auth_result.ok:
            try:
                parsed_fut = client.get_balances(omit_zero=True)
                balances = [
                    {
                        "asset": b.asset,
                        "free": b.available_balance,
                        "locked": b.as_testnet_balance().locked,
                        "total": b.wallet_balance,
                        "wallet_balance": b.wallet_balance,
                        "available_balance": b.available_balance,
                        "unrealized_profit": b.unrealized_profit,
                    }
                    for b in parsed_fut
                ]
                if not balances:
                    issues.append("Cuenta futures testnet sin balances no-cero.")
                tn_balances = [b.as_testnet_balance() for b in parsed_fut]
                strat = assess_strategy_funds(tn_balances, symbol=symbol)
                strategy = {
                    "symbol": strat.symbol,
                    "base_asset": strat.base_asset,
                    "quote_asset": strat.quote_asset,
                    "has_quote_usdt": strat.has_quote_usdt,
                    "quote_free": strat.quote_free,
                    "base_free": strat.base_free,
                    "min_notional_usdt": strat.min_notional_usdt,
                    "sufficient_for_strategy": strat.sufficient_for_strategy,
                    "notes": list(strat.notes),
                }
                if not strat.sufficient_for_strategy:
                    issues.append(
                        "Fondos insuficientes para estrategia mínima en "
                        f"{symbol} (ver strategy.notes)."
                    )
            except ValidationError as exc:
                issues.append(f"No se pudieron leer balances futures: {exc}")

    routing = _quantlab_routing_status()
    if routing["transport"] != "binance_futures_testnet":
        issues.append(
            "QuantLab no está en transport binance_futures_testnet "
            f"(actual: {routing['transport']})."
        )

    ready = not issues and connectivity is not None and connectivity.get("ok") is True
    return {
        "market": "futures",
        "testnet_ready": ready,
        "futures_testnet_ready": ready,
        "base_url": FUTURES_TESTNET_BASE_URL,
        "production_blocked": True,
        "connectivity": connectivity,
        "auth": auth,
        "balances": balances,
        "strategy": strategy,
        "quantlab_routing": routing,
        "hummingbot": hb,
        "issues": issues,
    }


def run_combined_testnet_diagnostic(
    *,
    symbol: str = _DEFAULT_SYMBOL,
    skip_network: bool = False,
) -> dict[str, Any]:
    """Diagnóstico Spot + Futures (sin órdenes)."""
    spot = run_testnet_diagnostic(symbol=symbol, skip_network=skip_network)
    futures = run_futures_testnet_diagnostic(symbol=symbol, skip_network=skip_network)
    conflict = remote_testnet_conflict()
    active_transport: str
    try:
        active_transport = resolve_demo_transport(
            unlocked=bool(live_unlock_status().get("unlocked"))
        )
    except ValidationError:
        active_transport = "conflict"
    return {
        "spot_ready": bool(spot.get("testnet_ready")),
        "futures_ready": bool(futures.get("testnet_ready")),
        "any_ready": bool(spot.get("testnet_ready") or futures.get("testnet_ready")),
        "conflict": conflict,
        "active_transport": active_transport,
        "production_blocked": True,
        "spot": spot,
        "futures": futures,
    }


def format_combined_diagnostic_report(payload: dict[str, Any]) -> str:
    lines = [
        "=== QuantLab dual testnet ===",
        f"SPOT READY: {'YES' if payload.get('spot_ready') else 'NO'}",
        f"FUTURES READY: {'YES' if payload.get('futures_ready') else 'NO'}",
        f"Active transport: {payload.get('active_transport')}",
        f"Conflict flags: {payload.get('conflict')}",
        f"Producción bloqueada: {payload.get('production_blocked')}",
        "",
        "----- SPOT -----",
        format_diagnostic_report(payload.get("spot") or {}),
        "----- FUTURES -----",
        format_diagnostic_report(payload.get("futures") or {}).replace(
            "TESTNET READY:", "FUTURES TESTNET READY:", 1
        ),
    ]
    return "\n".join(lines)


def format_diagnostic_report(payload: dict[str, Any]) -> str:
    """Informe legible para operador."""
    lines: list[str] = []
    ready = "YES" if payload.get("testnet_ready") else "NO"
    market = str(payload.get("market") or "spot").upper()
    lines.append(f"TESTNET READY: {ready}")
    lines.append(f"Market: {market}")
    lines.append("")
    lines.append(f"Base URL: {payload.get('base_url')}")
    lines.append(f"Producción bloqueada: {payload.get('production_blocked')}")
    lines.append("")

    conn = payload.get("connectivity") or {}
    lines.append("--- Conectividad ---")
    if conn.get("skipped"):
        lines.append("  (omitida)")
    else:
        lines.append(f"  OK: {conn.get('ok')}")
        lines.append(f"  Ping: {conn.get('ping_ok')}")
        lines.append(f"  Server time (ms): {conn.get('server_time_ms')}")
        if conn.get("error"):
            lines.append(f"  Error: {conn.get('error')}")
    lines.append("")

    auth = payload.get("auth") or {}
    lines.append("--- Autenticación ---")
    if not auth:
        lines.append("  (no evaluada)")
    else:
        lines.append(f"  OK: {auth.get('ok')}")
        lines.append(f"  canTrade: {auth.get('can_trade')}")
        lines.append(f"  uid: {auth.get('uid')}")
        if auth.get("error"):
            lines.append(f"  Error: {auth.get('error')}")
    lines.append("")

    balances = payload.get("balances") or []
    lines.append("--- Balances (no-cero) ---")
    if not balances:
        lines.append("  (sin datos)")
    else:
        for row in balances[:30]:
            lines.append(
                f"  {row['asset']}: free={row['free']} locked={row['locked']} total={row['total']}"
            )
        if len(balances) > 30:
            lines.append(f"  ... +{len(balances) - 30} activos más")
    lines.append("")

    strategy = payload.get("strategy")
    lines.append("--- Estrategia ---")
    if not strategy:
        lines.append("  (no evaluada)")
    else:
        lines.append(f"  Par: {strategy.get('symbol')}")
        lines.append(f"  USDT libre: {strategy.get('quote_free')}")
        lines.append(f"  Base libre: {strategy.get('base_free')}")
        lines.append(f"  Suficiente: {strategy.get('sufficient_for_strategy')}")
        for note in strategy.get("notes") or []:
            lines.append(f"  Nota: {note}")
    lines.append("")

    routing = payload.get("quantlab_routing") or {}
    lines.append("--- QuantLab routing ---")
    lines.append(f"  LIVE_BLOCKED: {routing.get('live_blocked')}")
    lines.append(f"  Transport: {routing.get('transport')}")
    lines.append(f"  Unlock: {routing.get('unlock', {}).get('unlocked')}")
    lines.append("")

    hb = payload.get("hummingbot") or {}
    lines.append("--- Hummingbot ---")
    lines.append(f"  Instalado: {hb.get('installed')}")
    lines.append(f"  Método: {hb.get('detection_method')}")
    lines.append(f"  Testnet spot soportado en HB: {hb.get('spot_testnet_connector_available')}")
    lines.append(f"  Recomendación: {hb.get('recommendation')}")
    lines.append("")

    issues = payload.get("issues") or []
    lines.append("--- Problemas ---")
    if not issues:
        lines.append("  (ninguno)")
    else:
        for issue in issues:
            lines.append(f"  - {issue}")

    return "\n".join(lines) + "\n"
