"""CLI de diagnóstico A3 (seguro por defecto)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from quantlab.core.types.enums import IntentType, OrderSide, OrderType, TimeInForce
from quantlab.core.types.orders import OrderIntent
from quantlab.data.exchanges.a3.adapter import A3Adapter
from quantlab.data.exchanges.a3.config import A3Config, load_a3_config, load_credentials_from_env
from quantlab.data.exchanges.a3.constants import A3EnvironmentName
from quantlab.data.exchanges.a3.fake_backend import FakeA3Backend


def _print_env(config_env: str, execution_enabled: bool) -> None:
    print(f"ENVIRONMENT: {config_env.upper()}")
    if config_env == A3EnvironmentName.PRODUCTION.value:
        print("EXECUTION: DISABLED" if not execution_enabled else "EXECUTION: ENABLED")


def build_adapter(project_root: Path, *, use_fake: bool) -> tuple[A3Adapter, A3Config]:
    cfg = load_a3_config(project_root / "config" / "exchanges" / "a3.yaml")
    backend: FakeA3Backend | Any
    if use_fake:
        backend = FakeA3Backend()
        account = "SIM-FAKE"
    else:
        from quantlab.data.exchanges.a3.client import PyRofexBackend

        creds = load_credentials_from_env()
        backend = PyRofexBackend(creds, cfg.environment)
        account = creds.account
    adapter = A3Adapter(cfg, backend, account=account)
    adapter.connect()
    return adapter, cfg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quantlab-a3")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--live-api",
        action="store_true",
        help="Usar pyRofex real (requiere credenciales). Default: fake offline.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health")
    sub.add_parser("instruments")
    p_md = sub.add_parser("market-data")
    p_md.add_argument("symbol")
    p_hist = sub.add_parser("historical")
    p_hist.add_argument("symbol")
    p_hist.add_argument("--days", type=int, default=1)
    p_hist.add_argument("--timeframe", default="1m")
    sub.add_parser("account")
    sub.add_parser("positions")
    p_sim = sub.add_parser("simulation-order")
    p_sim.add_argument("symbol")
    p_sim.add_argument("--qty", default="1")
    p_sim.add_argument("--price", default="1000")

    args = parser.parse_args(argv)
    adapter, cfg = build_adapter(args.root, use_fake=not args.live_api)
    _print_env(cfg.environment.value, cfg.execution.enabled)

    try:
        if args.cmd == "health":
            print(adapter.health_check())
        elif args.cmd == "instruments":
            for inst in adapter.get_instruments():
                print(inst.symbol, inst.instrument_id)
        elif args.cmd == "market-data":
            snap = adapter.get_market_snapshot(args.symbol)
            print(snap.symbol, snap.last_price, len(snap.bids), len(snap.offers))
        elif args.cmd == "historical":
            end = datetime.now(tz=UTC)
            start = end - timedelta(days=args.days)
            bars, manifest = adapter.get_historical_bars(args.symbol, args.timeframe, start, end)
            print("bars", len(bars), "dataset", manifest.dataset_id)
        elif args.cmd == "account":
            print(adapter.get_account_summary())
        elif args.cmd == "positions":
            for pos in adapter.get_positions():
                print(pos.symbol, pos.quantity)
        elif args.cmd == "simulation-order":
            if cfg.is_production:
                print("ERROR: simulation-order no permitido en production")
                return 2
            # Requiere execution.enabled en config para pasar risk; con fake
            # usamos intent mínimo — el adapter rechazará si execution disabled.
            intent = OrderIntent(
                intent_id="cli-sim-1",
                intent_type=IntentType.PLACE_ORDER,
                instrument_id=f"a3:{args.symbol}",
                side=OrderSide.BUY,
                quantity=Decimal(args.qty),
                price=Decimal(args.price),
                order_type=OrderType.LIMIT,
                time_in_force=TimeInForce.GTC,
            )
            # Snapshot para freshness
            adapter.get_market_snapshot(args.symbol)
            try:
                ack = adapter.place_order(intent)
                print("placed", ack.order_id, ack.status)
                if ack.order_id:
                    canceled = adapter.cancel_order(ack.order_id)
                    print("canceled", canceled.status)
            except Exception as exc:
                print("rejected:", type(exc).__name__, str(exc))
                return 1
        return 0
    finally:
        adapter.close()


if __name__ == "__main__":
    raise SystemExit(main())
