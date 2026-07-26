"""F51 — Soft API rate limit in-process (IP/path token bucket).

Default alto (120 req/s); tests inyectan límite bajo y esperan 429 JSON.
"""

from __future__ import annotations

import http.client
import json
from http.server import ThreadingHTTPServer

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.about import PHASES_SUMMARY
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.rate_limit import (
    DEFAULT_RATE_LIMIT_BURST,
    DEFAULT_RATE_LIMIT_RPS,
    RateLimitConfig,
    RateLimiter,
    rate_limit_error_payload,
)


def test_live_blocked_invariant_f51() -> None:
    assert LIVE_BLOCKED is True


def test_version_and_phases_f51() -> None:
    assert __version__ == "0.85.0"
    assert PHASES_SUMMARY == "F19–F93 INTERNAL"


def test_default_rate_limit_is_high() -> None:
    assert DEFAULT_RATE_LIMIT_RPS >= 120.0
    assert DEFAULT_RATE_LIMIT_BURST >= 120.0
    lim = RateLimiter()
    assert lim.config.requests_per_second == DEFAULT_RATE_LIMIT_RPS
    # Default no debe disparar 429 en ráfaga moderada típica de tests.
    for _ in range(50):
        d = lim.allow("127.0.0.1", "/api/mode")
        assert d.allowed is True


def test_token_bucket_blocks_when_exhausted() -> None:
    lim = RateLimiter(
        RateLimitConfig(enabled=True, requests_per_second=1.0, burst=2.0)
    )
    assert lim.allow("10.0.0.1", "/api/health").allowed is True
    assert lim.allow("10.0.0.1", "/api/health").allowed is True
    blocked = lim.allow("10.0.0.1", "/api/health")
    assert blocked.allowed is False
    assert blocked.retry_after_s > 0
    payload = rate_limit_error_payload(blocked)
    assert payload["ok"] is False
    assert payload["code"] == "rate_limit_exceeded"
    # Otras rutas / IPs son buckets independientes.
    assert lim.allow("10.0.0.1", "/api/mode").allowed is True
    assert lim.allow("10.0.0.2", "/api/health").allowed is True


def test_rate_limit_disabled() -> None:
    lim = RateLimiter(
        RateLimitConfig(enabled=False, requests_per_second=1.0, burst=1.0)
    )
    for _ in range(20):
        assert lim.allow("127.0.0.1", "/api/about").allowed is True


def test_http_429_with_low_injected_limit(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    """Inyecta límite bajo; exceder → 429 JSON + Retry-After."""
    assert LIVE_BLOCKED is True
    server, state = workbench_server
    state.configure_rate_limit(
        RateLimitConfig(enabled=True, requests_per_second=2.0, burst=2.0)
    )
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)

    statuses: list[int] = []
    bodies: list[dict[str, object]] = []
    for _ in range(5):
        conn = http.client.HTTPConnection(host, port, timeout=5.0)
        try:
            conn.request("GET", "/api/mode")
            resp = conn.getresponse()
            raw = resp.read()
            statuses.append(resp.status)
            if resp.status == 429:
                assert resp.getheader("Retry-After") is not None
                bodies.append(json.loads(raw.decode("utf-8")))
        finally:
            conn.close()

    assert statuses.count(200) == 2
    assert statuses.count(429) == 3
    assert all(b.get("ok") is False for b in bodies)
    assert all(b.get("code") == "rate_limit_exceeded" for b in bodies)
    assert all("error" in b for b in bodies)


def test_http_default_limit_allows_burst(
    workbench_server: tuple[ThreadingHTTPServer, WorkbenchState],
) -> None:
    """Con default 120 rps, una ráfaga corta de tests no debe 429."""
    server, _state = workbench_server
    host, port = server.server_address[:2]
    assert isinstance(host, str)
    assert isinstance(port, int)
    for _ in range(30):
        conn = http.client.HTTPConnection(host, port, timeout=5.0)
        try:
            conn.request("GET", "/api/about")
            resp = conn.getresponse()
            raw = resp.read()
            assert resp.status == 200, raw
        finally:
            conn.close()
