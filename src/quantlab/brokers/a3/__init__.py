"""Adapter A3 como BrokerPort (MD-only; fake|env read-only)."""

from quantlab.brokers.a3.adapter_port import A3BrokerPort
from quantlab.brokers.a3.md_backend import (
    MD_READONLY_ENV,
    MD_SOURCE_ENV,
    MD_SOURCE_FAKE,
    resolve_a3_md_backend,
)

__all__ = [
    "A3BrokerPort",
    "MD_SOURCE_FAKE",
    "MD_SOURCE_ENV",
    "MD_READONLY_ENV",
    "resolve_a3_md_backend",
]
