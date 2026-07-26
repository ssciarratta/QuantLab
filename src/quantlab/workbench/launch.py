"""CLI entry point: quantlab-workbench."""

from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser
from collections.abc import Sequence

from quantlab.brokers.mode import OperatingMode, default_mode, resolve_mode
from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.server import create_server

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantlab-workbench",
        description="QuantLab Workbench — UI local loopback (Fase 20).",
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
        "--no-browser",
        action="store_true",
        help="No abrir el navegador automáticamente",
    )
    parser.add_argument(
        "--mode",
        default=default_mode().value,
        help="Modo de sesión: tester|paper|real (live rechazado)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

    if not LIVE_BLOCKED:
        print("ABORT: LIVE_BLOCKED=False — workbench no arranca", file=sys.stderr)
        return 2

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

    host = str(args.host)
    port = int(args.port)
    state = WorkbenchState(mode=mode)
    server = create_server(host=host, port=port, state=state)
    bound_host, bound_port = server.server_address[:2]
    # server_address tipado como (str | bytes, int) en stdlib
    host_s = bound_host.decode() if isinstance(bound_host, bytes) else str(bound_host)
    url = f"http://{host_s}:{int(bound_port)}/"

    print(f"QuantLab Workbench v0.14 — {url}")
    print(f"mode={mode.value}  LIVE_BLOCKED={LIVE_BLOCKED}  real_alias=paper")
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
