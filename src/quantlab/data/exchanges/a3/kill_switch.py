"""Kill switch persistente."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from quantlab.data.exchanges.a3.constants import KillSwitchScope


@dataclass(frozen=True, slots=True)
class KillSwitchState:
    block_all_orders: bool = False
    block_production: bool = True
    blocked_accounts: tuple[str, ...] = ()
    blocked_symbols: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "block_all_orders": self.block_all_orders,
            "block_production": self.block_production,
            "blocked_accounts": list(self.blocked_accounts),
            "blocked_symbols": list(self.blocked_symbols),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> KillSwitchState:
        accounts = data.get("blocked_accounts") or []
        symbols = data.get("blocked_symbols") or []
        if not isinstance(accounts, list):
            accounts = []
        if not isinstance(symbols, list):
            symbols = []
        return cls(
            block_all_orders=bool(data.get("block_all_orders", False)),
            block_production=bool(data.get("block_production", True)),
            blocked_accounts=tuple(str(x) for x in accounts),
            blocked_symbols=tuple(str(x) for x in symbols),
        )


class KillSwitch:
    """Por defecto bloquea producción. No se reactiva implícitamente."""

    def __init__(self, path: Path) -> None:
        self._path = path
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self.save(KillSwitchState())

    def load(self) -> KillSwitchState:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return KillSwitchState.from_dict(data)

    def save(self, state: KillSwitchState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")

    def is_blocked(
        self,
        *,
        is_production: bool,
        account: str | None,
        symbol: str | None,
    ) -> tuple[bool, str | None]:
        state = self.load()
        if state.block_all_orders:
            return True, KillSwitchScope.ALL_ORDERS.value
        if is_production and state.block_production:
            return True, KillSwitchScope.PRODUCTION_ONLY.value
        if account and account in state.blocked_accounts:
            return True, KillSwitchScope.ACCOUNT.value
        if symbol and symbol in state.blocked_symbols:
            return True, KillSwitchScope.SYMBOL.value
        return False, None
