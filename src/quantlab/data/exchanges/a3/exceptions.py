"""Excepciones del adaptador A3."""

from __future__ import annotations

from quantlab.core.exceptions import QuantLabError


class A3Error(QuantLabError):
    """Error base de integración A3."""


class A3ConfigurationError(A3Error):
    """Configuración inválida o incompleta."""


class A3AuthenticationError(A3Error):
    """Fallo de autenticación / credenciales."""


class A3ConnectionError(A3Error):
    """Fallo de conectividad REST/WS."""


class A3ProtocolError(A3Error):
    """Respuesta de protocolo inesperada."""


class A3RateLimitError(A3Error):
    """Límite de tasa / throttling."""


class A3DataError(A3Error):
    """Datos de mercado inválidos o corruptos."""


class A3MappingError(A3Error):
    """Fallo al mapear DTO externo → dominio."""


class A3SubscriptionError(A3Error):
    """Fallo de suscripción WebSocket."""


class A3OrderRejectedError(A3Error):
    """Orden rechazada por el venue / API."""


class A3RiskRejectedError(A3Error):
    """Orden bloqueada por risk gate local."""


class A3LiveTradingDisabledError(A3Error):
    """Intento de orden en producción sin gates."""


class A3ReconciliationError(A3Error):
    """Fallo de reconciliación de órdenes."""
