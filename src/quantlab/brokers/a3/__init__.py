"""Adapter A3 como BrokerPort (MD-only; fake|env read-only)."""

from quantlab.brokers.a3.adapter_port import A3BrokerPort
from quantlab.brokers.a3.md_backend import (
    MD_READONLY_ENV,
    MD_SOURCE_ENV,
    MD_SOURCE_FAKE,
    a3_md_capability_status,
    resolve_a3_md_backend,
)
from quantlab.brokers.a3.read_contract import (
    A3ReadContractReport,
    A3ReadContractStatus,
    run_fake_read_contract,
    run_sandbox_read_contract_from_env,
)

__all__ = [
    "A3BrokerPort",
    "MD_SOURCE_FAKE",
    "MD_SOURCE_ENV",
    "MD_READONLY_ENV",
    "resolve_a3_md_backend",
    "a3_md_capability_status",
    "A3ReadContractReport",
    "A3ReadContractStatus",
    "run_fake_read_contract",
    "run_sandbox_read_contract_from_env",
]
