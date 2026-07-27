"""Memoria conversacional del chat (sesión durable)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError

MAX_HISTORY_TURNS = 40
MAX_MESSAGE_CHARS = 4000


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str
    tools_used: list[str] = field(default_factory=list)
    provider: str = "fake"
    ts: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "tools_used": list(self.tools_used),
            "provider": self.provider,
            "ts": self.ts,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ChatMessage:
        role = str(raw.get("role") or "user")
        if role not in {"user", "assistant", "system"}:
            raise ValidationError(f"role inválido: {role}")
        content = str(raw.get("content") or "")
        tools = raw.get("tools_used")
        tools_used = [str(t) for t in tools] if isinstance(tools, list) else []
        provider = str(raw.get("provider") or "fake")
        ts = str(raw.get("ts") or datetime.now(tz=UTC).isoformat())
        return cls(
            role=role,
            content=content[:MAX_MESSAGE_CHARS],
            tools_used=tools_used,
            provider=provider,
            ts=ts,
        )


@dataclass
class ChatMemory:
    """Historial multi-turno en memoria + persistencia opcional."""

    messages: list[ChatMessage] = field(default_factory=list)
    max_turns: int = MAX_HISTORY_TURNS

    def append_user(self, content: str) -> None:
        text = content.strip()
        if not text:
            raise ValidationError("mensaje vacío")
        self.messages.append(ChatMessage(role="user", content=text[:MAX_MESSAGE_CHARS]))
        self._trim()

    def append_assistant(
        self,
        content: str,
        *,
        tools_used: list[str] | None = None,
        provider: str = "fake",
    ) -> None:
        self.messages.append(
            ChatMessage(
                role="assistant",
                content=content[:MAX_MESSAGE_CHARS],
                tools_used=list(tools_used or []),
                provider=provider,
            )
        )
        self._trim()

    def clear(self) -> None:
        self.messages.clear()

    def _trim(self) -> None:
        if len(self.messages) > self.max_turns:
            self.messages = self.messages[-self.max_turns :]

    def recent(self, n: int = 12) -> list[ChatMessage]:
        if n < 1:
            return []
        return list(self.messages[-n:])

    def for_llm(self, n: int = 16) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for msg in self.recent(n):
            if msg.role in {"user", "assistant"}:
                out.append({"role": msg.role, "content": msg.content})
        return out

    def summary_text(self, n: int = 6) -> str:
        lines: list[str] = []
        for msg in self.recent(n):
            prefix = "Usuario" if msg.role == "user" else "Asistente"
            snippet = msg.content.replace("\n", " ")[:180]
            lines.append(f"{prefix}: {snippet}")
        return "\n".join(lines)

    def last_exchange(self) -> tuple[ChatMessage | None, ChatMessage | None]:
        last_user: ChatMessage | None = None
        last_assistant: ChatMessage | None = None
        for msg in reversed(self.messages):
            if msg.role == "assistant" and last_assistant is None:
                last_assistant = msg
            elif msg.role == "user" and last_user is None:
                last_user = msg
            if last_user and last_assistant:
                break
        return last_user, last_assistant

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "count": len(self.messages),
            "messages": [m.to_dict() for m in self.messages],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ChatMemory:
        mem = cls()
        items = raw.get("messages")
        if not isinstance(items, list):
            return mem
        for item in items:
            if isinstance(item, dict):
                mem.messages.append(ChatMessage.from_dict(item))
        mem._trim()
        return mem

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> ChatMemory:
        if not path.is_file():
            return cls()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        if not isinstance(raw, dict):
            return cls()
        return cls.from_dict(raw)
