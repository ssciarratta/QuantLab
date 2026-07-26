"""Sesión durable del workbench (journal, book, meta, labs, chat audit)."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from quantlab.brokers.paper.book import DEFAULT_INITIAL_CASH, PaperBook
from quantlab.brokers.paper.journal import PaperFillJournal
from quantlab.brokers.paper.reconciliation import JournalCheckpoint, reconcile_book
from quantlab.core.exceptions import ValidationError
from quantlab.data.atomic_io import atomic_write_text

DEFAULT_SESSION_PARENT = Path("data/runtime/workbench")

# Fail-closed: session_id es segmento de path; sin separators / traversal.
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


@dataclass(frozen=True, slots=True)
class LoadedPaperBook:
    """Book cargado junto con metadatos de durabilidad."""

    book: PaperBook
    checkpoint: JournalCheckpoint | None
    schema_version: int


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
    def equity_path(self) -> Path:
        return self._root / "equity.jsonl"

    @property
    def access_path(self) -> Path:
        return self._root / "access.jsonl"

    @property
    def layout_path(self) -> Path:
        return self._root / "layout.json"

    @property
    def presets_dir(self) -> Path:
        return self._root / "presets"

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

    @property
    def backups_dir(self) -> Path:
        return self._root / "backups"

    def ensure_layout(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.features_dir.mkdir(parents=True, exist_ok=True)
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        self.optimizer_dir.mkdir(parents=True, exist_ok=True)
        self.montecarlo_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        if not self.journal_path.exists():
            self.journal_path.touch()
        if not self.chat_audit_path.exists():
            self.chat_audit_path.touch()
        if not self.activity_path.exists():
            self.activity_path.touch()
        if not self.equity_path.exists():
            self.equity_path.touch()
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
        return self.load_book_state(default_cash=default_cash).book

    def load_book_state(
        self, *, default_cash: Decimal = DEFAULT_INITIAL_CASH
    ) -> LoadedPaperBook:
        """Carga v2 o el formato flat legado sin ocultar su provenance."""
        if self.book_path.exists():
            try:
                raw = json.loads(self.book_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise ValidationError(f"book.json inválido: {exc}") from exc
            if not isinstance(raw, dict):
                raise ValidationError("book.json inválido")
            if raw.get("schema_version") == 2:
                book_payload = raw.get("book")
                checkpoint_payload = raw.get("journal_checkpoint")
                if not isinstance(book_payload, dict):
                    raise ValidationError("book.json v2 requiere objeto book")
                if not isinstance(checkpoint_payload, dict):
                    raise ValidationError("book.json v2 requiere journal_checkpoint")
                return LoadedPaperBook(
                    book=PaperBook.from_dict(book_payload),
                    checkpoint=JournalCheckpoint.from_dict(checkpoint_payload),
                    schema_version=2,
                )
            if "schema_version" in raw:
                raise ValidationError(
                    f"book.json schema_version no soportada: {raw.get('schema_version')!r}"
                )
            return LoadedPaperBook(
                book=PaperBook.from_dict(raw),
                checkpoint=None,
                schema_version=1,
            )
        return LoadedPaperBook(
            book=PaperBook(initial_cash=default_cash),
            checkpoint=None,
            schema_version=0,
        )

    def save_book(
        self,
        book: PaperBook,
        checkpoint: JournalCheckpoint | None = None,
    ) -> None:
        """Persiste proyección v2 atómicamente, ligada al journal durable."""
        self.ensure_layout()
        journal = PaperFillJournal(self.journal_path)
        report = reconcile_book(book, journal)
        if not report.ok or report.checkpoint is None:
            raise ValidationError(
                f"book no reconciliado; persist rechazado: {'; '.join(report.issues)}"
            )
        resolved_checkpoint = checkpoint or report.checkpoint
        if resolved_checkpoint != report.checkpoint:
            raise ValidationError("checkpoint provisto no coincide con journal actual")
        payload = {
            "schema_version": 2,
            "book": book.to_dict(),
            "journal_checkpoint": resolved_checkpoint.to_dict(),
        }
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        atomic_write_text(self.book_path, text)

    def to_dict(self) -> dict[str, Any]:
        meta = self.load_meta()
        return {
            "session_id": self._session_id,
            "root": str(self._root.resolve()),
            "journal": str(self.journal_path),
            "book": str(self.book_path),
            "meta": str(self.meta_path),
            "layout": str(self.layout_path),
            "presets": str(self.presets_dir),
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
            "equity": str(self.equity_path),
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
            journal = PaperFillJournal(session.journal_path)
            try:
                journal_empty = journal.checkpoint().record_count == 0
            except ValidationError:
                journal_empty = False
            if journal_empty:
                session.save_book(PaperBook(initial_cash=cash))
        return session
