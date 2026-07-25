"""Tests de configure_logging / get_logger."""

from __future__ import annotations

import structlog

from quantlab.infra.config.models import LoggingConfig
from quantlab.infra.logging import configure_logging, get_logger
from quantlab.infra.logging.setup import configure_logging as configure_logging_direct


def test_configure_logging_json_uses_json_renderer() -> None:
    configure_logging(LoggingConfig(level="DEBUG", json_output=True))
    processors = structlog.get_config()["processors"]
    assert any(type(p).__name__ == "JSONRenderer" for p in processors)
    log = get_logger("quantlab.test.json")
    log.info("evento_json", ok=True)


def test_configure_logging_console_uses_console_renderer() -> None:
    configure_logging(LoggingConfig(level="INFO", json_output=False))
    processors = structlog.get_config()["processors"]
    assert any(type(p).__name__ == "ConsoleRenderer" for p in processors)
    log = get_logger("quantlab.test.console")
    log.info("evento_console", ok=True)


def test_get_logger_returns_bound_logger() -> None:
    configure_logging_direct(LoggingConfig(level="WARNING", json_output=True))
    log = get_logger("quantlab.test.named")
    assert log is not None
    bound = log.bind(component="unit")
    bound.warning("aviso", code=1)
    assert hasattr(bound, "info")
    assert hasattr(bound, "error")
