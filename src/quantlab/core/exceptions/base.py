"""Excepciones base del sistema."""


class QuantLabError(Exception):
    """Error base de QuantLab."""


class DomainError(QuantLabError):
    """Violación de regla de dominio."""


class ValidationError(DomainError):
    """Error de validación de datos o contratos."""


class ConfigError(QuantLabError):
    """Error de carga o validación de configuración."""


class ManifestError(DomainError):
    """Error en manifests de dataset o experimento."""
