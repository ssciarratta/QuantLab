"""Tests audit log append-only del chat (Fase 22)."""

from __future__ import annotations

from pathlib import Path

from quantlab.workbench.api import WorkbenchState
from quantlab.workbench.chat.audit import ChatAuditLog
from quantlab.workbench.chat.orchestrator import ChatOrchestrator
from quantlab.workbench.chat.providers import FakeProvider


def test_audit_log_written(tmp_path: Path) -> None:
    audit_path = tmp_path / "chat_audit.jsonl"
    audit = ChatAuditLog(audit_path)
    orch = ChatOrchestrator(
        WorkbenchState(),
        provider=FakeProvider(),
        audit=audit,
    )
    out = orch.handle_message("salud del sistema")
    assert out["ok"] is True
    assert audit_path.is_file()
    rows = audit.read_all()
    assert len(rows) == 1
    assert rows[0]["event"] == "chat_turn"
    assert rows[0]["live_blocked"] is True
    assert "get_health" in rows[0]["tools_used"]
    assert "salud" in rows[0]["message"].lower()

    orch.handle_message("política live")
    rows2 = audit.read_all()
    assert len(rows2) == 2
    # append-only: primera línea intacta
    assert rows2[0]["message"] == rows[0]["message"]
