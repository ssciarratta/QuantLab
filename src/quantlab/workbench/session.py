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


def resolve_session_parent(parent: Path | None = None) -> Path:
    """Resuelve el parent de sesiones (default ``data/runtime/workbench``)."""
    root = Path(parent) if parent is not None else DEFAULT_SESSION_PARENT
    return root.resolve()


def list_sessions(parent: Path | None = None) -> list[dict[str, Any]]:
    """Lista directorios de sesión bajo ``parent`` (solo IDs válidos).

    Fail-closed: ignora entradas que no pasen ``validate_session_id`` o
    que escapen del parent vía symlink/traversal.
    """
    root = resolve_session_parent(parent)
    if not root.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        try:
            sid = validate_session_id(child.name)
        except ValidationError:
            continue
        try:
            resolved = child.resolve()
        except OSError:
            continue
        if not resolved.is_relative_to(root):
            continue
        meta: dict[str, Any] = {}
        meta_path = resolved / "meta.json"
        if meta_path.is_file():
            try:
                raw = json.loads(meta_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    meta = raw
            except (OSError, json.JSONDecodeError, UnicodeError):
                meta = {}
        created = meta.get("created_at")
        items.append(
            {
                "session_id": sid,
                "root": str(resolved),
                "created_at": created if isinstance(created, str) else None,
                "has_book": (resolved / "book.json").is_file(),
                "has_meta": meta_path.is_file(),
            }
        )
    return items


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

    @property
    def activity_path(self) -> Path:
        return self._root / "activity.jsonl"

    @property
    def access_path(self) -> Path:
        return self._root / "access.jsonl"

    @property
    def layout_path(self) -> Path:
        return self._root / "layout.json"

    @property
    def settings_path(self) -> Path:
        return self._root / "settings.json"

    @property
    def reports_dir(self) -> Path:
        return self._root / "reports"

    @property
    def watchlist_path(self) -> Path:
        return self._root / "watchlist.json"

    @property
    def features_dir(self) -> Path:
        return self._root / "features"

    @property
    def validation_dir(self) -> Path:
        return self._root / "validation"

    @property
    def optimizer_dir(self) -> Path:
        return self._root / "optimizer"

    @property
    def montecarlo_dir(self) -> Path:
        return self._root / "montecarlo"

    def ensure_layout(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.features_dir.mkdir(parents=True, exist_ok=True)
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        self.optimizer_dir.mkdir(parents=True, exist_ok=True)
        self.montecarlo_dir.mkdir(parents=True, exist_ok=True)
        if not self.journal_path.exists():
            self.journal_path.touch()
        if not self.chat_audit_path.exists():
            self.chat_audit_path.touch()
        if not self.activity_path.exists():
            self.activity_path.touch()
        if not self.access_path.exists():
            self.access_path.touch()

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
            "layout": str(self.layout_path),
            "settings": str(self.settings_path),
            "watchlist": str(self.watchlist_path),
            "experiments": str(self.experiments_dir),
            "exports": str(self.exports_dir),
            "reports": str(self.reports_dir),
            "features": str(self.features_dir),
            "validation": str(self.validation_dir),
            "optimizer": str(self.optimizer_dir),
            "montecarlo": str(self.montecarlo_dir),
            "chat_audit": str(self.chat_audit_path),
            "activity": str(self.activity_path),
            "access": str(self.access_path),
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
