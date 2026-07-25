"""Setup de logging estructurado con structlog."""

from __future__ import annotations

import logging
from typing import Any

import structlog

from quantlab.infra.config.models import LoggingConfig


def configure_logging(config: LoggingConfig) -> None:
    """Configura structlog + stdlib logging según AppConfig."""
    level = getattr(logging, config.level.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if config.json_output:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [structlog.dev.ConsoleRenderer()]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(format="%(message)s", level=level, force=True)


def get_logger(name: str) -> Any:
    """Retorna logger estructurado."""
    return structlog.get_logger(name)
