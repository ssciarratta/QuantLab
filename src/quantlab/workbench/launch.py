"""CLI entry point: quantlab-workbench."""

from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

from quantlab.brokers.mode import OperatingMode, default_mode, resolve_mode
from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.server import create_server, is_loopback_host
from quantlab.workbench.session import DEFAULT_SESSION_PARENT, WorkbenchSession

# Re-export para tests / callers F25.
__all__ = (
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "build_parser",
    "is_loopback_host",
    "main",
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantlab-workbench",
        description="QuantLab Workbench — UI local loopback (Fase 20–25).",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Bind address (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Puerto HTTP (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--allow-non-loopback",
        action="store_true",
        help="Permitir bind fuera de loopback (riesgo; warning stderr)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="No abrir el navegador automáticamente",
    )
    parser.add_argument(
        "--mode",
        default=default_mode().value,
        help="Modo de sesión: tester|paper|real (live rechazado)",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="ID de sesión durable (default: UUID corto nuevo)",
    )
    parser.add_argument(
        "--session-root",
        default=None,
        help=f"Parent de sesiones (default: {DEFAULT_SESSION_PARENT})",
    )
    parser.add_argument(
        "--initial-cash",
        default=str(DEFAULT_INITIAL_CASH),
        help=f"Cash inicial del PaperBook (default: {DEFAULT_INITIAL_CASH})",
    )
    parser.add_argument(
        "--slippage-bps",
        default="0",
        help="Slippage paper adverso en bps (default: 0)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

    if not LIVE_BLOCKED:
        print("ABORT: LIVE_BLOCKED=False — workbench no arranca", file=sys.stderr)
        return 2

    host = str(args.host)
    if not is_loopback_host(host) and not args.allow_non_loopback:
        print(
            f"ABORT: host={host!r} no es loopback. "
            "Usar 127.0.0.1/::1/localhost o pasar --allow-non-loopback.",
            file=sys.stderr,
        )
        return 2
    if not is_loopback_host(host) and args.allow_non_loopback:
        print(
            f"WARNING: bind non-loopback host={host!r} (sin auth HTTP; no exponer a WAN).",
            file=sys.stderr,
        )

    try:
        mode = resolve_mode(str(args.mode))
    except ValidationError as exc:
        print(f"modo inválido: {exc}", file=sys.stderr)
        return 2
    if mode is OperatingMode.LIVE:
        print(
            "OperatingMode.LIVE bloqueado en workbench (LIVE_BLOCKED). "
            "Usar --mode tester|paper|real.",
            file=sys.stderr,
        )
        return 2

    try:
        initial_cash = Decimal(str(args.initial_cash))
    except (InvalidOperation, ValueError) as exc:
        print(f"initial-cash inválido: {exc}", file=sys.stderr)
        return 2
    if initial_cash < 0:
        print("initial-cash no puede ser negativo", file=sys.stderr)
        return 2

    try:
        slippage_bps = Decimal(str(args.slippage_bps))
    except (InvalidOperation, ValueError) as exc:
        print(f"slippage-bps inválido: {exc}", file=sys.stderr)
        return 2
    if slippage_bps < 0:
        print("slippage-bps no puede ser negativo", file=sys.stderr)
        return 2
    if slippage_bps >= Decimal("10000"):
        print("slippage-bps debe ser < 10000", file=sys.stderr)
        return 2

    root_parent = Path(args.session_root) if args.session_root else None
    try:
        session = WorkbenchSession.create_or_load(
            root_parent,
            args.session_id,
            initial_cash=initial_cash,
        )
    except ValidationError as exc:
        print(f"sesión inválida: {exc}", file=sys.stderr)
        return 2

    port = int(args.port)
    state = WorkbenchState(
        mode=mode,
        session=session,
        initial_cash=initial_cash,
        slippage_bps=slippage_bps,
    )
    state.ensure_session()
    server = create_server(
        host=host,
        port=port,
        state=state,
        allow_non_loopback=bool(args.allow_non_loopback),
    )
    bound_host, bound_port = server.server_address[:2]
    # server_address tipado como (str | bytes, int) en stdlib
    host_s = bound_host.decode() if isinstance(bound_host, bytes) else str(bound_host)
    url = f"http://{host_s}:{int(bound_port)}/"

    print(f"QuantLab Workbench v0.17 — {url}")
    print(f"mode={mode.value}  LIVE_BLOCKED={LIVE_BLOCKED}  real_alias=paper")
    print(f"session_id={session.session_id}  root={session.root}")
    print(f"slippage_bps={slippage_bps}")
    print("Chat: asistente research (safe-mode) — no envía órdenes.")
    print("Ctrl+C para detener.")

    if not args.no_browser:

        def _open() -> None:
            time.sleep(0.35)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo workbench…")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
