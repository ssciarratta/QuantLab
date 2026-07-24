"""Tests for logging setup."""

from __future__ import annotations

import logging

from quantlab.infra.config import load_config
from quantlab.infra.logging import setup_logging


class TestLoggingSetup:
    def test_console_logging(self):
        config = load_config()
        logger = setup_logging(config)
        assert logger is not None

    def test_json_logging(self):
        config = load_config(environment="research")
        logger = setup_logging(config)
        assert logger is not None

    def test_log_level_applied(self):
        config = load_config(overrides={"logging": {"level": "DEBUG", "format": "console"}})
        setup_logging(config)
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_log_level_warning(self):
        config = load_config(overrides={"logging": {"level": "WARNING", "format": "console"}})
        setup_logging(config)
        root = logging.getLogger()
        assert root.level == logging.WARNING
