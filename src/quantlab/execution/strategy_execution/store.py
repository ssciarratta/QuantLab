"""Persistencia local de promociones y sesiones de ejecución."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.execution.strategy_execution.destinations import ExecutionSessionState
from quantlab.execution.strategy_execution.manifest import StrategyPromotionManifest


@dataclass
class ExecutionSessionRecord:
    session_id: str
    promotion_id: str
    state: ExecutionSessionState
    created_at: str
    updated_at: str
    manifest: StrategyPromotionManifest
    configuration_revisions: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    paper_session_running: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "promotion_id": self.promotion_id,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "manifest": self.manifest.to_dict(),
            "configuration_revisions": self.configuration_revisions,
            "events": self.events[-200:],
            "error": self.error,
            "paper_session_running": self.paper_session_running,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionSessionRecord:
        return cls(
            session_id=str(data["session_id"]),
            promotion_id=str(data["promotion_id"]),
            state=ExecutionSessionState(str(data.get("state", "DRAFT"))),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            manifest=StrategyPromotionManifest.from_dict(data["manifest"]),
            configuration_revisions=list(data.get("configuration_revisions") or []),
            events=list(data.get("events") or []),
            error=data.get("error"),
            paper_session_running=bool(data.get("paper_session_running")),
        )


class ExecutionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.promotions_dir = root / "promotions"
        self.sessions_dir = root / "sessions"
        self.promotions_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def save_promotion(self, manifest: StrategyPromotionManifest) -> None:
        path = self.promotions_dir / f"{manifest.promotion_id}.json"
        path.write_text(
            json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_promotion(self, promotion_id: str) -> StrategyPromotionManifest:
        path = self.promotions_dir / f"{promotion_id}.json"
        if not path.is_file():
            raise FileNotFoundError(promotion_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return StrategyPromotionManifest.from_dict(data)

    def save_session(self, rec: ExecutionSessionRecord) -> None:
        path = self.sessions_dir / f"{rec.session_id}.json"
        path.write_text(
            json.dumps(rec.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_session(self, session_id: str) -> ExecutionSessionRecord:
        path = self.sessions_dir / f"{session_id}.json"
        if not path.is_file():
            raise FileNotFoundError(session_id)
        return ExecutionSessionRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list_sessions(self) -> list[ExecutionSessionRecord]:
        out: list[ExecutionSessionRecord] = []
        for path in sorted(self.sessions_dir.glob("*.json")):
            try:
                out.append(
                    ExecutionSessionRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
                )
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
        return out

    def find_active_session(self) -> ExecutionSessionRecord | None:
        active = {
            ExecutionSessionState.STARTING,
            ExecutionSessionState.RUNNING,
            ExecutionSessionState.PAUSED,
            ExecutionSessionState.UPDATING,
            ExecutionSessionState.STOPPING,
        }
        for rec in self.list_sessions():
            if rec.state in active:
                return rec
        return None


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
