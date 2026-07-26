"""Soft in-process API rate limit (F51) — token bucket por IP/path.

Default alto (120 req/s) para no romper tests/perf; inyectable en tests.
Loopback soft: sin Redis/auth WAN; solo protección local del ThreadingHTTPServer.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

# Default generoso: no debe interferir con suites ni baseline F50.
DEFAULT_RATE_LIMIT_RPS: float = 120.0
DEFAULT_RATE_LIMIT_BURST: float = 120.0


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    """Configuración soft del rate limiter in-process."""

    enabled: bool = True
    requests_per_second: float = DEFAULT_RATE_LIMIT_RPS
    burst: float = DEFAULT_RATE_LIMIT_BURST

    def __post_init__(self) -> None:
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be > 0")
        if self.burst <= 0:
            raise ValueError("burst must be > 0")


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """Resultado de ``allow``: permitido o 429."""

    allowed: bool
    retry_after_s: float = 0.0
    limit: float = 0.0
    remaining: float = 0.0
    key: str = ""

    @property
    def message(self) -> str:
        if self.allowed:
            return "ok"
        wait = max(0.001, self.retry_after_s)
        return (
            f"rate limit exceeded ({self.limit:.0f} req/s per IP/path); "
            f"retry after {wait:.3f}s"
        )


class TokenBucket:
    """Token bucket thread-safe (refill continuo)."""

    __slots__ = ("_capacity", "_tokens", "_refill_per_s", "_updated", "_lock")

    def __init__(self, *, capacity: float, refill_per_s: float) -> None:
        self._capacity = float(capacity)
        self._tokens = float(capacity)
        self._refill_per_s = float(refill_per_s)
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens: float = 1.0) -> tuple[bool, float, float]:
        """Intenta consumir tokens.

        Returns:
            (allowed, remaining, retry_after_s)
        """
        need = float(tokens)
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._updated
            if elapsed > 0:
                self._tokens = min(
                    self._capacity,
                    self._tokens + elapsed * self._refill_per_s,
                )
                self._updated = now
            if self._tokens >= need:
                self._tokens -= need
                return True, self._tokens, 0.0
            deficit = need - self._tokens
            retry = deficit / self._refill_per_s if self._refill_per_s > 0 else 1.0
            return False, self._tokens, retry


class RateLimiter:
    """Rate limiter in-process keyed by ``(client_ip, path)``."""

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self._config = config if config is not None else RateLimitConfig()
        self._buckets: dict[str, TokenBucket] = {}
        self._map_lock = threading.Lock()

    @property
    def config(self) -> RateLimitConfig:
        return self._config

    def _make_key(self, client_ip: str, path: str) -> str:
        ip = (client_ip or "unknown").strip() or "unknown"
        p = (path or "/").split("?", 1)[0] or "/"
        return f"{ip}|{p}"

    def _bucket_for(self, key: str) -> TokenBucket:
        with self._map_lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(
                    capacity=self._config.burst,
                    refill_per_s=self._config.requests_per_second,
                )
                self._buckets[key] = bucket
            return bucket

    def allow(self, client_ip: str, path: str) -> RateLimitDecision:
        """True si la request puede continuar; False → 429."""
        cfg = self._config
        key = self._make_key(client_ip, path)
        if not cfg.enabled:
            return RateLimitDecision(
                allowed=True,
                limit=cfg.requests_per_second,
                remaining=cfg.burst,
                key=key,
            )
        bucket = self._bucket_for(key)
        ok, remaining, retry = bucket.consume(1.0)
        return RateLimitDecision(
            allowed=ok,
            retry_after_s=retry,
            limit=cfg.requests_per_second,
            remaining=max(0.0, remaining),
            key=key,
        )

    def reset(self) -> None:
        """Limpia buckets (útil en tests)."""
        with self._map_lock:
            self._buckets.clear()


def rate_limit_error_payload(decision: RateLimitDecision) -> dict[str, object]:
    """Payload JSON estándar 429."""
    retry = max(0.001, decision.retry_after_s)
    return {
        "ok": False,
        "error": decision.message,
        "code": "rate_limit_exceeded",
        "limit_rps": decision.limit,
        "retry_after_s": round(retry, 3),
    }
