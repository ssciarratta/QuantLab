"""CLI diagnóstico Binance Spot + Futures Testnet (sin órdenes)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from quantlab.brokers.binance.demo_transport import demo_transport_status
from quantlab.brokers.binance.futures_testnet_client import (
    BinanceFuturesTestnetClient,
    futures_testnet_keys_configured,
    public_futures_connectivity_check,
)
from quantlab.brokers.binance.testnet_client import (
    BinanceTestnetClient,
    public_connectivity_check,
    testnet_keys_configured,
)
from quantlab.brokers.binance.testnet_diagnostic import (
    format_combined_diagnostic_report,
    format_diagnostic_report,
    run_combined_testnet_diagnostic,
    run_futures_testnet_diagnostic,
    run_testnet_diagnostic,
)
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_unlock import live_unlock_status
from quantlab.execution_export.hummingbot_probe import (
    hummingbot_status,
    verify_hummingbot_testnet_safety,
)


def _load_dotenv_if_present(root: Path) -> None:
    """Carga .env local si existe (sin imprimir valores)."""
    import os

    env_path = root / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def _cmd_status(_args: argparse.Namespace) -> int:
    unlocked = bool(live_unlock_status().get("unlocked"))
    payload = demo_transport_status(unlocked=unlocked)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if payload.get("conflict") else 0


def _cmd_ping(args: argparse.Namespace) -> int:
    market = args.market
    results: dict[str, Any] = {}
    ok_all = True
    if market in {"spot", "all"}:
        conn = public_connectivity_check()
        results["spot"] = {
            "ok": conn.ok,
            "ping_ok": conn.ping_ok,
            "server_time_ms": conn.server_time_ms,
            "base_url": conn.base_url,
            "error": conn.error,
        }
        ok_all = ok_all and conn.ok
    if market in {"futures", "all"}:
        conn_f = public_futures_connectivity_check()
        results["futures"] = {
            "ok": conn_f.ok,
            "ping_ok": conn_f.ping_ok,
            "server_time_ms": conn_f.server_time_ms,
            "base_url": conn_f.base_url,
            "error": conn_f.error,
        }
        ok_all = ok_all and conn_f.ok
    print(json.dumps(results, indent=2))
    return 0 if ok_all else 1


def _cmd_balances(args: argparse.Namespace) -> int:
    market = args.market
    if market == "futures":
        if not futures_testnet_keys_configured():
            print(
                "ERROR: BINANCE_FUTURES_DEMO_API_KEY/SECRET no configuradas.",
                file=sys.stderr,
            )
            return 2
        client_f = BinanceFuturesTestnetClient()
        auth = client_f.auth_check()
        if not auth.ok:
            print(f"ERROR: autenticación futures falló: {auth.error}", file=sys.stderr)
            return 3
        balances_f = client_f.get_balances(omit_zero=True)
        payload = [
            {
                "asset": b.asset,
                "available": b.available_balance,
                "wallet": b.wallet_balance,
                "unrealized_profit": b.unrealized_profit,
            }
            for b in balances_f
        ]
        print(
            json.dumps(
                {"ok": True, "market": "futures", "count": len(payload), "balances": payload},
                indent=2,
            )
        )
        return 0

    if not testnet_keys_configured():
        print("ERROR: BINANCE_DEMO_API_KEY/SECRET no configuradas.", file=sys.stderr)
        return 2
    client = BinanceTestnetClient()
    auth = client.auth_check()
    if not auth.ok:
        print(f"ERROR: autenticación falló: {auth.error}", file=sys.stderr)
        return 3
    balances = client.get_balances(omit_zero=True)
    payload = [
        {"asset": b.asset, "free": b.free, "locked": b.locked, "total": b.total}
        for b in balances
    ]
    print(
        json.dumps(
            {"ok": True, "market": "spot", "count": len(payload), "balances": payload},
            indent=2,
        )
    )
    return 0


def _cmd_diagnostic(args: argparse.Namespace) -> int:
    market = args.market
    if market == "all":
        payload = run_combined_testnet_diagnostic(
            symbol=args.symbol,
            skip_network=args.skip_network,
        )
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(format_combined_diagnostic_report(payload), end="")
        return 0 if payload.get("any_ready") else 1

    if market == "futures":
        payload = run_futures_testnet_diagnostic(
            symbol=args.symbol,
            skip_network=args.skip_network,
        )
    else:
        payload = run_testnet_diagnostic(
            symbol=args.symbol,
            skip_network=args.skip_network,
        )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_diagnostic_report(payload), end="")
    return 0 if payload.get("testnet_ready") else 1


def _cmd_hummingbot(_args: argparse.Namespace) -> int:
    print(json.dumps(hummingbot_status(), indent=2, sort_keys=True))
    return 0


def _cmd_hb_verify(_args: argparse.Namespace) -> int:
    result = verify_hummingbot_testnet_safety()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quantlab-testnet",
        description=(
            "Diagnóstico Binance Spot + Futures Testnet "
            "(sin órdenes, sin producción)."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Raíz del proyecto (para cargar .env local).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Estado Spot+Futures flags/keys (sin red).")
    p_ping = sub.add_parser("ping", help="Conectividad pública testnet.")
    p_ping.add_argument(
        "--market",
        choices=("spot", "futures", "all"),
        default="all",
        help="Mercado a sondear (default: all).",
    )
    p_bal = sub.add_parser("balances", help="Balances firmados (requiere keys).")
    p_bal.add_argument(
        "--market",
        choices=("spot", "futures"),
        default="spot",
        help="Mercado (default: spot).",
    )
    p_diag = sub.add_parser(
        "diagnostic",
        help="Diagnóstico TESTNET READY (spot|futures|all).",
    )
    p_diag.add_argument("--symbol", default="BTCUSDT")
    p_diag.add_argument("--json", action="store_true")
    p_diag.add_argument(
        "--market",
        choices=("spot", "futures", "all"),
        default="spot",
        help="Default spot (compat scripts 07). Use all para dual.",
    )
    p_diag.add_argument(
        "--skip-network",
        action="store_true",
        help="Omitir llamadas de red (solo config local).",
    )
    # Alias explícito
    p_fdiag = sub.add_parser(
        "futures-diagnostic",
        help="Alias de diagnostic --market futures.",
    )
    p_fdiag.add_argument("--symbol", default="BTCUSDT")
    p_fdiag.add_argument("--json", action="store_true")
    p_fdiag.add_argument("--skip-network", action="store_true")

    sub.add_parser("hummingbot", help="Estado Hummingbot externo.")
    sub.add_parser("hb-verify", help="Verifica configs HB vs producción.")

    args = parser.parse_args(argv)
    _load_dotenv_if_present(args.root)

    if args.cmd == "futures-diagnostic":
        args.market = "futures"
        args.cmd = "diagnostic"

    handlers: dict[str, Any] = {
        "status": _cmd_status,
        "ping": _cmd_ping,
        "balances": _cmd_balances,
        "diagnostic": _cmd_diagnostic,
        "hummingbot": _cmd_hummingbot,
        "hb-verify": _cmd_hb_verify,
    }
    try:
        return int(handlers[args.cmd](args))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
