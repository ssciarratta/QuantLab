"""ChatOrchestrator — orquesta provider + tools + audit (safe-by-default)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.audit import ChatAuditLog
from quantlab.workbench.chat.providers import ChatProvider, FakeProvider, build_default_provider
from quantlab.workbench.chat.tools import ALLOWED_TOOLS, ToolRegistry


class ChatOrchestrator:
    """Entrada única del chat workbench. Nunca mutea LIVE ni envía órdenes."""

    def __init__(
        self,
        state: WorkbenchState,
        *,
        provider: ChatProvider | None = None,
        audit: ChatAuditLog | None = None,
        docs_root: Path | None = None,
    ) -> None:
        self._state = state
        self._tools = ToolRegistry(state, docs_root=docs_root)
        self._provider: ChatProvider = (
            provider if provider is not None else build_default_provider()
        )
        self._audit = audit if audit is not None else ChatAuditLog()

    @property
    def audit_path(self) -> Path:
        return self._audit.path

    @property
    def tools(self) -> ToolRegistry:
        return self._tools

    def list_tools(self) -> dict[str, Any]:
        return {
            "ok": True,
            "tools": self._tools.list_allowlist(),
            "allowlist": sorted(ALLOWED_TOOLS),
            "live_blocked": LIVE_BLOCKED is True,
            "safe_mode": True,
            "mutations_allowed": False,
        }

    def handle_message(self, message: str) -> dict[str, Any]:
        if not isinstance(message, str) or not message.strip():
            raise ValidationError("campo 'message' requerido (string no vacío)")
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True; chat aborta")

        turn = self._provider.complete(message.strip(), self._tools)
        payload = {
            "ok": True,
            "reply": turn.reply,
            "tools_used": list(turn.tools_used),
            "mode": self._state.mode.value,
            "live_blocked": LIVE_BLOCKED is True,
            "safe_mode": True,
            "provider": turn.provider,
        }
        self._audit.append(
            {
                "event": "chat_turn",
                "message": message.strip()[:2000],
                "reply_preview": turn.reply[:500],
                "tools_used": list(turn.tools_used),
                "mode": self._state.mode.value,
                "live_blocked": True,
                "provider": turn.provider,
            }
        )
        return payload


def build_orchestrator(
    state: WorkbenchState,
    *,
    provider: ChatProvider | None = None,
    audit_path: Path | None = None,
) -> ChatOrchestrator:
    audit = ChatAuditLog(audit_path) if audit_path is not None else ChatAuditLog()
    return ChatOrchestrator(
        state,
        provider=provider if provider is not None else FakeProvider(),
        audit=audit,
    )
