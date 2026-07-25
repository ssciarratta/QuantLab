"""Configuración tipada de A3 (sin secretos)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from quantlab.data.exchanges.a3.constants import A3EnvironmentName
from quantlab.data.exchanges.a3.exceptions import A3ConfigurationError


@dataclass(frozen=True, slots=True)
class A3Credentials:
    """Credenciales desde entorno — nunca loguear."""

    user: str
    password: str
    account: str
    token: str | None = None


@dataclass(frozen=True, slots=True)
class A3RiskConfig:
    max_order_quantity: Decimal
    max_notional: Decimal | None
    symbol_allowlist: tuple[str, ...]
    reject_if_insufficient_info: bool
    max_market_data_age_seconds: int


@dataclass(frozen=True, slots=True)
class A3ExecutionConfig:
    enabled: bool
    allow_live_orders: bool
    account_allowlist: tuple[str, ...]
    require_live_confirmation: bool


@dataclass(frozen=True, slots=True)
class A3StorageConfig:
    raw_root: Path
    processed_root: Path
    catalog_path: Path
    kill_switch_path: Path


@dataclass(frozen=True, slots=True)
class A3MarketDataConfig:
    enabled: bool
    websocket: bool
    depth: int
    reconnect: bool
    queue_maxsize: int


@dataclass(frozen=True, slots=True)
class A3Config:
    enabled: bool
    environment: A3EnvironmentName
    market_data: A3MarketDataConfig
    execution: A3ExecutionConfig
    storage: A3StorageConfig
    risk: A3RiskConfig
    websocket_backoff_initial: float = 1.0
    websocket_backoff_max: float = 60.0

    @property
    def is_production(self) -> bool:
        return self.environment is A3EnvironmentName.PRODUCTION


def load_credentials_from_env() -> A3Credentials:
    user = os.environ.get("QUANTLAB_A3_USER", "").strip()
    password = os.environ.get("QUANTLAB_A3_PASSWORD", "").strip()
    account = os.environ.get("QUANTLAB_A3_ACCOUNT", "").strip()
    token = os.environ.get("QUANTLAB_A3_TOKEN", "").strip() or None
    if not user or not password or not account:
        raise A3ConfigurationError(
            "Faltan QUANTLAB_A3_USER / QUANTLAB_A3_PASSWORD / QUANTLAB_A3_ACCOUNT"
        )
    return A3Credentials(user=user, password=password, account=account, token=token)


def live_trading_env_enabled() -> bool:
    from quantlab.data.exchanges.a3.constants import LIVE_TRADING_CONFIRMATION

    return os.environ.get("QUANTLAB_ENABLE_LIVE_TRADING", "DISABLED") == LIVE_TRADING_CONFIRMATION


def load_a3_config(path: Path) -> A3Config:
    if not path.exists():
        raise A3ConfigurationError(f"No existe config A3: {path}")
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        env = A3EnvironmentName(str(raw.get("environment", "simulation")))
        md = raw.get("market_data") or {}
        ex = raw.get("execution") or {}
        st = raw.get("storage") or {}
        risk = raw.get("risk") or {}
        ws = raw.get("websocket") or {}
        max_qty = Decimal(str(risk.get("max_order_quantity", "1")))
        max_notional = risk.get("max_notional")
        return A3Config(
            enabled=bool(raw.get("enabled", False)),
            environment=env,
            market_data=A3MarketDataConfig(
                enabled=bool(md.get("enabled", True)),
                websocket=bool(md.get("websocket", True)),
                depth=int(md.get("depth", 5)),
                reconnect=bool(md.get("reconnect", True)),
                queue_maxsize=int(md.get("queue_maxsize", 10000)),
            ),
            execution=A3ExecutionConfig(
                enabled=bool(ex.get("enabled", False)),
                allow_live_orders=bool(ex.get("allow_live_orders", False)),
                account_allowlist=tuple(str(x) for x in (ex.get("account_allowlist") or [])),
                require_live_confirmation=bool(ex.get("require_live_confirmation", True)),
            ),
            storage=A3StorageConfig(
                raw_root=Path(str(st.get("raw_root", "data/raw/a3"))),
                processed_root=Path(str(st.get("processed_root", "data/processed/a3"))),
                catalog_path=Path(
                    str(st.get("catalog_path", "data/catalog/quantlab_catalog.sqlite"))
                ),
                kill_switch_path=Path(
                    str(st.get("kill_switch_path", "data/runtime/kill_switch.json"))
                ),
            ),
            risk=A3RiskConfig(
                max_order_quantity=max_qty,
                max_notional=None if max_notional is None else Decimal(str(max_notional)),
                symbol_allowlist=tuple(str(x) for x in (risk.get("symbol_allowlist") or [])),
                reject_if_insufficient_info=bool(risk.get("reject_if_insufficient_info", True)),
                max_market_data_age_seconds=int(risk.get("max_market_data_age_seconds", 30)),
            ),
            websocket_backoff_initial=float(ws.get("backoff_initial_seconds", 1)),
            websocket_backoff_max=float(ws.get("backoff_max_seconds", 60)),
        )
    except (TypeError, ValueError, KeyError) as exc:
        raise A3ConfigurationError(f"Config A3 inválida: {exc}") from exc
