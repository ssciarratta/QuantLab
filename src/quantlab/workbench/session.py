"""Sesión durable del workbench (journal, book, meta, labs, chat audit)."""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH, PaperBook
from quantlab.core.exceptions import ValidationError

DEFAULT_SESSION_PARENT = Path("data/runtime/workbench")

# Fail-closed: session_id es segmento de path; sin separators / traversal.
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def validate_session_id(session_id: str) -> str:
    """Valida ``session_id`` seguro para usar como segmento de path."""
    sid = session_id.strip()
    if not sid or sid in {".", ".."} or not _SESSION_ID_RE.fullmatch(sid):
        raise ValidationError(
            f"session_id inválido (solo [A-Za-z0-9._-], 1–64 chars, "
            f"sin path separators): {session_id!r}"
        )
    if "/" in sid or "\\" in sid or ".." in sid:
        raise ValidationError(f"session_id con path traversal rechazado: {session_id!r}")
    return sid


class WorkbenchSession:
    """Root durable: ``<parent>/<session_id>/`` con journal/book/meta/labs/audit."""

    def __init__(self, root: Path, session_id: str) -> None:
        self._root = root
        self._session_id = validate_session_id(session_id)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def journal_path(self) -> Path:
        return self._root / "journal.jsonl"

    @property
    def book_path(self) -> Path:
        return self._root / "book.json"

    @property
    def meta_path(self) -> Path:
        return self._root / "meta.json"

    @property
    def experiments_dir(self) -> Path:
        return self._root / "experiments"

    @property
    def exports_dir(self) -> Path:
        return self._root / "exports"

    @property
    def chat_audit_path(self) -> Path:
        return self._root / "chat_audit.jsonl"

    def ensure_layout(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        if not self.journal_path.exists():
            self.journal_path.touch()
        if not self.chat_audit_path.exists():
            self.chat_audit_path.touch()

    def load_meta(self) -> dict[str, Any]:
        if not self.meta_path.exists():
            return {}
        raw = json.loads(self.meta_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValidationError("meta.json inválido")
        return raw

    def save_meta(self, meta: dict[str, Any]) -> None:
        self.ensure_layout()
        payload = dict(meta)
        payload.setdefault("session_id", self._session_id)
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        self.meta_path.write_text(text, encoding="utf-8")

    def load_book(self, *, default_cash: Decimal = DEFAULT_INITIAL_CASH) -> PaperBook:
        if self.book_path.exists():
            raw = json.loads(self.book_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValidationError("book.json inválido")
            return PaperBook.from_dict(raw)
        return PaperBook(initial_cash=default_cash)

    def save_book(self, book: PaperBook) -> None:
        self.ensure_layout()
        text = json.dumps(book.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        self.book_path.write_text(text, encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        meta = self.load_meta()
        return {
            "session_id": self._session_id,
            "root": str(self._root.resolve()),
            "journal": str(self.journal_path),
            "book": str(self.book_path),
            "meta": str(self.meta_path),
            "experiments": str(self.experiments_dir),
            "exports": str(self.exports_dir),
            "chat_audit": str(self.chat_audit_path),
            "meta_payload": meta,
        }

    @classmethod
    def create_or_load(
        cls,
        root_parent: Path | None,
        session_id: str | None,
        *,
        initial_cash: Decimal | None = None,
    ) -> WorkbenchSession:
        parent = Path(root_parent) if root_parent is not None else DEFAULT_SESSION_PARENT
        parent = parent.resolve()
        parent.mkdir(parents=True, exist_ok=True)
        raw_sid = (session_id or "").strip() or uuid.uuid4().hex[:12]
        sid = validate_session_id(raw_sid)
        root = (parent / sid).resolve()
        if not root.is_relative_to(parent):
            raise ValidationError(
                f"session root fuera de parent (path traversal): {root} vs {parent}"
            )
        session = cls(root=root, session_id=sid)
        session.ensure_layout()
        cash = initial_cash if initial_cash is not None else DEFAULT_INITIAL_CASH
        if not session.meta_path.exists():
            session.save_meta(
                {
                    "session_id": sid,
                    "created_at": datetime.now(tz=UTC).isoformat(),
                    "initial_cash": str(cash),
                }
            )
        if not session.book_path.exists():
            session.save_book(PaperBook(initial_cash=cash))
        return session
