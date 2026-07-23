"""Base exception hierarchy for QuantLab."""


class QuantLabError(Exception):
    """Base exception for all QuantLab errors."""


class ValidationError(QuantLabError):
    """Raised when domain validation fails."""


class ConfigurationError(QuantLabError):
    """Raised when configuration is invalid or missing."""


class DataError(QuantLabError):
    """Raised when data operations fail."""


class SimulationError(QuantLabError):
    """Raised when simulation encounters an error."""


class StrategyError(QuantLabError):
    """Raised when a strategy encounters an error."""
