"""CLI diagnóstico Binance Spot Testnet (sin órdenes)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from quantlab.brokers.binance.testnet_client import (
    BinanceTestnetClient,
    public_connectivity_check,
    testnet_keys_configured,
    testnet_status,
)
from quantlab.brokers.binance.testnet_diagnostic import (
    format_diagnostic_report,
    run_testnet_diagnostic,
)
from quantlab.core.exceptions import ValidationError
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
    print(json.dumps(testnet_status(), indent=2, sort_keys=True))
    return 0


def _cmd_ping(_args: argparse.Namespace) -> int:
    conn = public_connectivity_check()
    print(json.dumps(
        {
            "ok": conn.ok,
            "ping_ok": conn.ping_ok,
            "server_time_ms": conn.server_time_ms,
            "base_url": conn.base_url,
            "error": conn.error,
        },
        indent=2,
    ))
    return 0 if conn.ok else 1


def _cmd_balances(_args: argparse.Namespace) -> int:
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
    print(json.dumps({"ok": True, "count": len(payload), "balances": payload}, indent=2))
    return 0


def _cmd_diagnostic(args: argparse.Namespace) -> int:
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
        description="Diagnóstico Binance Spot Testnet (sin órdenes, sin producción).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Raíz del proyecto (para cargar .env local).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Estado de flags/keys testnet (sin red).")
    sub.add_parser("ping", help="Conectividad pública testnet (ping + time).")
    sub.add_parser("balances", help="Balances firmados (requiere keys).")
    p_diag = sub.add_parser("diagnostic", help="Diagnóstico integral TESTNET READY.")
    p_diag.add_argument("--symbol", default="BTCUSDT")
    p_diag.add_argument("--json", action="store_true")
    p_diag.add_argument(
        "--skip-network",
        action="store_true",
        help="Omitir llamadas de red (solo config local).",
    )
    sub.add_parser("hummingbot", help="Estado Hummingbot externo.")
    sub.add_parser("hb-verify", help="Verifica configs HB vs producción.")

    args = parser.parse_args(argv)
    _load_dotenv_if_present(args.root)

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
