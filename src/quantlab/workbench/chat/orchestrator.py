"""ChatOrchestrator — memoria, contexto y provider (safe-by-default)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.audit import ChatAuditLog
from quantlab.workbench.chat.context import build_assistant_context, build_system_prompt
from quantlab.workbench.chat.memory import ChatMemory
from quantlab.workbench.chat.providers import (
    ChatProvider,
    ChatRequest,
    build_default_provider,
)
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

    def memory(self) -> ChatMemory:
        if self._state.chat_memory is None:
            session = self._state.ensure_session()
            self._state.chat_memory = ChatMemory.load(session.chat_history_path)
        mem: ChatMemory = self._state.chat_memory
        return mem

    def persist_memory(self) -> None:
        mem = self.memory()
        session = self._state.ensure_session()
        mem.save(session.chat_history_path)

    def list_tools(self) -> dict[str, Any]:
        return {
            "ok": True,
            "tools": self._tools.list_allowlist(),
            "allowlist": sorted(ALLOWED_TOOLS),
            "live_blocked": LIVE_BLOCKED is True,
            "safe_mode": True,
            "mutations_allowed": False,
            "memory_turns": len(self.memory().messages),
        }

    def history_payload(self) -> dict[str, Any]:
        mem = self.memory()
        return {
            "ok": True,
            "count": len(mem.messages),
            "messages": [m.to_dict() for m in mem.messages],
            "live_blocked": LIVE_BLOCKED is True,
        }

    def clear_history(self) -> dict[str, Any]:
        self.memory().clear()
        self._state.chat_instructor_ctx = {}
        self.persist_memory()
        return {"ok": True, "cleared": True, "count": 0}

    def handle_message(
        self,
        message: str,
        *,
        ui_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(message, str) or not message.strip():
            raise ValidationError("campo 'message' requerido (string no vacío)")
        if not LIVE_BLOCKED:
            raise ValidationError("LIVE_BLOCKED debe ser True; chat aborta")

        mem = self.memory()
        mem.append_user(message.strip())
        ctx = build_assistant_context(self._state, mem, ui_context=ui_context)
        request = ChatRequest(
            message=message.strip(),
            history=tuple(mem.recent(20)),
            ui_context=ui_context,
            assistant_context=ctx,
            system_prompt=build_system_prompt(ctx),
        )

        turn = self._provider.complete(request, self._tools)
        mem.append_assistant(turn.reply, tools_used=turn.tools_used, provider=turn.provider)
        self.persist_memory()

        payload = {
            "ok": True,
            "reply": turn.reply,
            "tools_used": list(turn.tools_used),
            "actions": list(turn.actions),
            "mode": self._state.mode.value,
            "live_blocked": LIVE_BLOCKED is True,
            "safe_mode": True,
            "provider": turn.provider,
            "memory_turns": len(mem.messages),
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
                "memory_turns": len(mem.messages),
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
        provider=provider if provider is not None else build_default_provider(),
        audit=audit,
    )
