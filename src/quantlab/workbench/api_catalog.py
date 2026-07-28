"""API route catalog + minimal OpenAPI 3 schema (F55).

Generated from a static documented catalog — **no FastAPI**.
Research-safe only: no LIVE trading routes (no place_order venue / set_live).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY

OPENAPI_VERSION = "3.0.3"
OPENAPI_PATH = "/api/openapi.json"

# Tokens that must never appear in path/summary (LIVE trading). `/api/livez` is OK.
_FORBIDDEN_LIVE_TOKENS: frozenset[str] = frozenset(
    {
        "place_order",
        "set_live",
        "flip_live",
        "live_order",
        "live_trading",
        "submit_live",
        "venue_order",
    }
)


@dataclass(frozen=True, slots=True)
class ApiRoute:
    """Documented HTTP route for the workbench API catalog."""

    path: str
    method: str
    summary: str
    tags: tuple[str, ...] = ()


# Catálogo canónico (paths/methods/summary). Path templates usan {param}.
API_ROUTES: tuple[ApiRoute, ...] = (
    # Meta / ops
    ApiRoute("/api/openapi.json", "GET", "OpenAPI 3 schema (API catalog)", ("meta",)),
    ApiRoute("/api/health", "GET", "Health report (rich)", ("ops",)),
    ApiRoute(
        "/api/diagnostics",
        "GET",
        "Read-only aggregate snapshot (version/mode/health/reconciliation)",
        ("ops",),
    ),
    ApiRoute(
        "/api/diagnostics.json",
        "GET",
        "Download diagnostics snapshot as JSON attachment (support bundle)",
        ("ops",),
    ),
    ApiRoute(
        "/api/support-bundle.zip",
        "GET",
        "Download read-only support ZIP (diagnostics/about/openapi/venues/recon)",
        ("ops",),
    ),
    ApiRoute("/api/livez", "GET", "Liveness probe", ("ops",)),
    ApiRoute("/api/readyz", "GET", "Readiness probe (LIVE_BLOCKED + writable)", ("ops",)),
    ApiRoute("/api/about", "GET", "About / version / phases INTERNAL", ("meta",)),
    ApiRoute(
        "/api/update/status",
        "GET",
        "Versión local vs GitHub + última modificación",
        ("meta", "ops"),
    ),
    ApiRoute(
        "/api/update/apply",
        "POST",
        "git pull --ff-only origin/main (+ uv sync); requiere reinicio",
        ("meta", "ops"),
    ),
    ApiRoute("/api/lab/sim/fees", "GET", "Fee presets VIP0 por venue", ("lab", "sim")),
    ApiRoute(
        "/api/lab/sim/period",
        "GET",
        "Estima N velas para period_days × interval",
        ("lab", "sim"),
    ),
    ApiRoute(
        "/api/lab/sim/compare",
        "POST",
        "Comparación multi-venue spot/futuros + leverage + bench",
        ("lab", "sim"),
    ),
    ApiRoute(
        "/api/lab/sim/sizing",
        "POST",
        "Valida capital / por trade / leverage",
        ("lab", "sim"),
    ),
    ApiRoute("/api/commands", "GET", "Command palette registry", ("meta",)),
    ApiRoute("/api/ops/metrics", "GET", "Ops metrics JSON", ("ops",)),
    ApiRoute("/api/ops/prometheus", "GET", "Prometheus text exposition", ("ops",)),
    ApiRoute("/api/shutdown", "POST", "Graceful shutdown (loopback only)", ("ops",)),
    # Mode / broker / paper (research-safe; REAL=PAPER ≠ LIVE)
    ApiRoute("/api/mode", "GET", "Operating mode + LIVE gate", ("mode",)),
    ApiRoute("/api/mode", "POST", "Set operating mode (PAPER/REAL alias)", ("mode",)),
    ApiRoute(
        "/api/live/status",
        "GET",
        "LIVE gate status + credential unlock state (no secrets)",
        ("live",),
    ),
    ApiRoute(
        "/api/live/unlock",
        "POST",
        "Unlock LIVE session with username/password (ephemeral; not persisted)",
        ("live",),
    ),
    ApiRoute(
        "/api/live/lock",
        "POST",
        "Lock LIVE session (revoke unlock)",
        ("live",),
    ),
    ApiRoute(
        "/api/live/demo/submit",
        "POST",
        "Binance demo simulated fill (requires unlock; local sim only)",
        ("live", "binance"),
    ),
    ApiRoute(
        "/api/live/demo/fills",
        "GET",
        "List Binance demo simulated fills for unlocked session",
        ("live", "binance"),
    ),
    ApiRoute(
        "/api/live/demo/open-orders",
        "GET",
        "List Binance demo resting orders (requires unlock)",
        ("live", "binance"),
    ),
    ApiRoute(
        "/api/live/demo/cancel",
        "POST",
        "Cancel Binance demo resting order (requires unlock)",
        ("live", "binance"),
    ),
    ApiRoute(
        "/api/lab/binance/scan",
        "POST",
        "Binance public USDT scan (read-only market data)",
        ("lab", "binance"),
    ),
    ApiRoute(
        "/api/lab/binance/scanner",
        "POST",
        "Binance alpha scanner on public klines (read-only)",
        ("lab", "binance"),
    ),
    ApiRoute(
        "/api/lab/alpha/profiles",
        "GET",
        "Alpha Scanner profile catalog + venue capabilities",
        ("lab", "alpha"),
    ),
    ApiRoute(
        "/api/lab/binance/pipeline",
        "POST",
        "Binance alpha scan + backtest top-N (read-only MD)",
        ("lab", "binance"),
    ),
    ApiRoute(
        "/api/lab/a3/md-status",
        "GET",
        "A3 MD capability status (env flag/creds; no secrets)",
        ("lab", "a3"),
    ),
    ApiRoute(
        "/api/venues",
        "GET",
        "Broker registry: venues, plugins (contract v1 read-only) and connection",
        ("broker",),
    ),
    ApiRoute("/api/broker/instruments", "GET", "List instruments", ("broker",)),
    ApiRoute("/api/broker/snapshot", "GET", "Market data snapshot", ("broker",)),
    ApiRoute("/api/broker/account", "GET", "Broker account (paper/real MD)", ("broker",)),
    ApiRoute("/api/broker/positions", "GET", "Broker positions", ("broker",)),
    ApiRoute(
        "/api/broker/heartbeat",
        "GET",
        "Broker heartbeat (health or disconnected)",
        ("broker",),
    ),
    ApiRoute("/api/broker/connect", "POST", "Connect broker venue", ("broker",)),
    ApiRoute(
        "/api/broker/reconnect",
        "POST",
        "Reconnect broker using last connect params from session meta",
        ("broker",),
    ),
    ApiRoute(
        "/api/broker/disconnect",
        "POST",
        "Disconnect broker; clear connected state; keep last connect for reconnect",
        ("broker",),
    ),
    ApiRoute("/api/paper/book", "GET", "Paper book state", ("paper",)),
    ApiRoute("/api/paper/fills", "GET", "Paper fills journal", ("paper",)),
    ApiRoute("/api/paper/fills.csv", "GET", "Paper fills journal as CSV download", ("paper",)),
    ApiRoute("/api/paper/equity", "GET", "Paper equity curve snapshots (JSONL)", ("paper",)),
    ApiRoute(
        "/api/paper/pnl",
        "GET",
        "Paper PnL summary (realized/unrealized/equity/cash)",
        ("paper",),
    ),
    ApiRoute(
        "/api/paper/reconciliation",
        "GET",
        "Read-only paper journal/book reconciliation status",
        ("paper",),
    ),
    ApiRoute(
        "/api/paper/reconciliation/rehydrate",
        "POST",
        "Reload session from disk after offline CLI rebuild (never rebuilds files)",
        ("paper",),
    ),
    ApiRoute("/api/paper/submit", "POST", "Submit paper order (simulated fills)", ("paper",)),
    ApiRoute("/api/paper/kill", "GET", "Paper kill switch status", ("paper", "risk")),
    ApiRoute(
        "/api/paper/kill",
        "POST",
        "Engage/disengage paper kill switch",
        ("paper", "risk"),
    ),
    ApiRoute("/api/paper/session/status", "GET", "Paper session runner status", ("paper",)),
    ApiRoute("/api/paper/session/start", "POST", "Start paper session runner", ("paper",)),
    ApiRoute("/api/paper/session/stop", "POST", "Stop paper session runner", ("paper",)),
    ApiRoute("/api/paper/session/step", "POST", "Step paper session runner", ("paper",)),
    # Session / workspace
    ApiRoute("/api/session", "GET", "Current workbench session", ("session",)),
    ApiRoute("/api/sessions", "GET", "List sessions under session root", ("session",)),
    ApiRoute("/api/sessions/switch", "POST", "Switch active session", ("session",)),
    ApiRoute("/api/sessions/new", "POST", "Create new session", ("session",)),
    ApiRoute("/api/session/export", "GET", "Export session ZIP", ("session",)),
    ApiRoute("/api/session/import", "POST", "Import session ZIP", ("session",)),
    ApiRoute("/api/activity", "GET", "Activity log", ("session",)),
    ApiRoute("/api/access-log", "GET", "HTTP access log (method/path/status/ms)", ("session",)),
    ApiRoute("/api/backups", "GET", "List session auto-backup ZIPs", ("session",)),
    ApiRoute(
        "/api/backups/run",
        "POST",
        "Trigger manual session auto-backup",
        ("session",),
    ),
    ApiRoute("/api/layout", "GET", "Workspace layout", ("workspace",)),
    ApiRoute("/api/layout", "PUT", "Save workspace layout", ("workspace",)),
    ApiRoute("/api/settings", "GET", "Workbench settings", ("workspace",)),
    ApiRoute("/api/settings", "PUT", "Save workbench settings", ("workspace",)),
    ApiRoute("/api/i18n/{locale}", "GET", "UI i18n dictionary (es default, en stub)", ("meta",)),
    ApiRoute("/api/presets", "GET", "Workspace presets", ("workspace",)),
    ApiRoute("/api/presets/apply", "POST", "Apply workspace preset", ("workspace",)),
    ApiRoute("/api/presets/save", "POST", "Save current layout as custom preset", ("workspace",)),
    ApiRoute(
        "/api/presets/{name}",
        "DELETE",
        "Delete custom workspace preset (builtins protected)",
        ("workspace",),
    ),
    ApiRoute("/api/onboarding", "GET", "Onboarding status", ("workspace",)),
    ApiRoute(
        "/api/onboarding/complete",
        "POST",
        "Mark onboarding complete",
        ("workspace",),
    ),
    ApiRoute("/api/docs", "GET", "Docs / help index", ("docs",)),
    ApiRoute("/api/docs/content", "GET", "Read docs markdown content", ("docs",)),
    ApiRoute("/api/watchlist", "GET", "Universe watchlist", ("universe",)),
    ApiRoute("/api/watchlist", "PUT", "Update watchlist", ("universe",)),
    ApiRoute(
        "/api/watchlist/export",
        "GET",
        "Export watchlist JSON download",
        ("universe",),
    ),
    ApiRoute(
        "/api/watchlist/import",
        "POST",
        "Import watchlist symbols merge/replace",
        ("universe",),
    ),
    ApiRoute("/api/universe", "GET", "Universe symbols", ("universe",)),
    ApiRoute("/api/catalog", "GET", "Data catalog datasets", ("universe",)),
    ApiRoute("/api/risk", "GET", "Paper risk limits", ("risk",)),
    ApiRoute(
        "/api/risk/utilization",
        "GET",
        "Paper risk utilization vs book/positions",
        ("risk",),
    ),
    # Lab
    ApiRoute("/api/lab/capabilities", "GET", "Lab capabilities", ("lab",)),
    ApiRoute("/api/lab/strategies", "GET", "Strategy catalog", ("lab",)),
    ApiRoute("/api/lab/metrics", "GET", "Lab metrics history", ("lab",)),
    ApiRoute("/api/lab/experiments", "GET", "Lab experiments list", ("lab",)),
    ApiRoute("/api/lab/backtest", "POST", "Run lab backtest", ("lab",)),
    ApiRoute("/api/lab/scanner", "POST", "Run alpha scanner", ("lab",)),
    ApiRoute("/api/lab/optimize", "POST", "Run optimizer", ("lab",)),
    ApiRoute("/api/lab/optimize/history", "GET", "Optimizer run history", ("lab",)),
    ApiRoute(
        "/api/lab/optimize/history/{run_id}",
        "GET",
        "Optimizer run detail",
        ("lab",),
    ),
    ApiRoute("/api/lab/montecarlo", "POST", "Run Monte Carlo", ("lab",)),
    ApiRoute("/api/lab/montecarlo/history", "GET", "Monte Carlo history", ("lab",)),
    ApiRoute(
        "/api/lab/montecarlo/history/{run_id}",
        "GET",
        "Monte Carlo run detail",
        ("lab",),
    ),
    ApiRoute(
        "/api/lab/montecarlo/history/{run_id}",
        "DELETE",
        "Delete Monte Carlo run",
        ("lab",),
    ),
    ApiRoute("/api/lab/validation", "GET", "Validation runs list", ("lab",)),
    ApiRoute(
        "/api/lab/validation/{run_id}",
        "GET",
        "Validation run detail",
        ("lab",),
    ),
    ApiRoute("/api/lab/validation/run", "POST", "Run walk-forward validation", ("lab",)),
    ApiRoute("/api/lab/features", "POST", "Run features pipeline", ("lab",)),
    ApiRoute("/api/lab/features/run", "POST", "Run features pipeline (alias)", ("lab",)),
    ApiRoute("/api/lab/features/store", "GET", "Feature store browser", ("lab",)),
    ApiRoute("/api/lab/export-hb", "POST", "Export Hummingbot artifacts", ("lab",)),
    ApiRoute("/api/lab/exports", "GET", "List HB exports", ("lab",)),
    ApiRoute("/api/lab/exports/{export_id}", "GET", "HB export detail", ("lab",)),
    ApiRoute("/api/lab/reports", "GET", "List lab reports", ("lab",)),
    ApiRoute("/api/lab/reports/{report_id}", "GET", "Lab report detail", ("lab",)),
    # Chat
    ApiRoute("/api/chat/tools", "GET", "Chat tool allowlist", ("chat",)),
    ApiRoute("/api/chat", "POST", "Chat completion (allowlisted tools)", ("chat",)),
)


def catalog_routes() -> tuple[ApiRoute, ...]:
    """Return the documented API route catalog."""
    return API_ROUTES


# Credential gate F100 + demo routing F101 — no son trading producción.
LIVE_CREDENTIAL_GATE_PATHS: frozenset[str] = frozenset(
    {
        "/api/live/status",
        "/api/live/unlock",
        "/api/live/lock",
        "/api/live/demo/submit",
        "/api/live/demo/fills",
        "/api/live/demo/open-orders",
        "/api/live/demo/cancel",
    }
)


def is_live_trading_path(path: str) -> bool:
    """True for LIVE *trading* paths (not liveness ni credential gate F100)."""
    p = path.lower().rstrip("/")
    if p == "/api/livez" or p.startswith("/api/livez/"):
        return False
    if p in LIVE_CREDENTIAL_GATE_PATHS:
        return False
    return p == "/api/live" or p.startswith("/api/live/")


def assert_no_live_trading_routes(routes: tuple[ApiRoute, ...] | None = None) -> None:
    """Fail-closed: catalog must not document LIVE trading endpoints."""
    items = routes if routes is not None else API_ROUTES
    for route in items:
        if is_live_trading_path(route.path):
            raise AssertionError(
                f"LIVE trading route forbidden in catalog: {route.method} {route.path}"
            )
        blob = f"{route.path} {route.summary}".lower()
        for token in _FORBIDDEN_LIVE_TOKENS:
            if token in blob:
                raise AssertionError(
                    f"LIVE trading marker {token!r} in catalog: "
                    f"{route.method} {route.path}"
                )


def _path_parameters(path: str) -> list[dict[str, Any]]:
    params: list[dict[str, Any]] = []
    for part in path.strip("/").split("/"):
        if part.startswith("{") and part.endswith("}") and len(part) > 2:
            name = part[1:-1]
            params.append(
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": f"Path parameter {name}",
                }
            )
    return params


def build_openapi_schema(
    *,
    routes: tuple[ApiRoute, ...] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Build a minimal OpenAPI 3 document from the route catalog."""
    items = routes if routes is not None else API_ROUTES
    assert_no_live_trading_routes(items)
    ver = version if version is not None else __version__

    paths: dict[str, dict[str, Any]] = {}
    for route in items:
        method = route.method.lower()
        op: dict[str, Any] = {
            "summary": route.summary,
            "operationId": _operation_id(route),
            "responses": {
                "200": {"description": "OK"},
            },
        }
        if route.tags:
            op["tags"] = list(route.tags)
        params = _path_parameters(route.path)
        if params:
            op["parameters"] = params
        if method in ("post", "put", "patch"):
            op["requestBody"] = {
                "required": False,
                "content": {
                    "application/json": {
                        "schema": {"type": "object", "additionalProperties": True}
                    }
                },
            }
        paths.setdefault(route.path, {})[method] = op

    return {
        "openapi": OPENAPI_VERSION,
        "info": {
            "title": "QuantLab Workbench API",
            "version": ver,
            "description": (
                "Minimal OpenAPI 3 catalog for the loopback workbench HTTP API. "
                "Research-safe: LIVE order routing blocked. REAL = PAPER (≠ LIVE)."
            ),
        },
        "servers": [{"url": "http://127.0.0.1:8765", "description": "Default loopback"}],
        "paths": paths,
        "x-quantlab": {
            "live_blocked": LIVE_BLOCKED is True,
            "live_routing": False,
            "research_safe": True,
            "phases_summary": PHASES_SUMMARY,
            "generator": "quantlab.workbench.api_catalog",
            "route_count": len(items),
        },
    }


def _operation_id(route: ApiRoute) -> str:
    safe = (
        route.path.strip("/")
        .replace("/", "_")
        .replace("{", "")
        .replace("}", "")
        .replace("-", "_")
        .replace(".", "_")
    )
    return f"{route.method.lower()}_{safe}"


def openapi_payload(
    *,
    routes: tuple[ApiRoute, ...] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Alias used by the HTTP handler — returns the OpenAPI document."""
    return build_openapi_schema(routes=routes, version=version)
