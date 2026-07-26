"""Auto-backup periódico de sesión (ZIP) — F63.

Settings ``auto_backup_minutes`` (default 0=off). Si >0, un thread daemon
exporta ZIP research-safe a ``session/backups/`` con rotación max 5.
Reutiliza allowlist + zip-slip de ``session_zip.export_session``.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.execution.live_gate import LIVE_BLOCKED
from quantlab.workbench.session import WorkbenchSession
from quantlab.workbench.session_zip import SessionExportResult, export_session
from quantlab.workbench.settings import (
    DEFAULT_AUTO_BACKUP_MINUTES,
    load_settings,
    parse_auto_backup_minutes,
)

logger = logging.getLogger(__name__)

BACKUPS_DIRNAME = "backups"
MAX_BACKUPS = 5
# Poll del scheduler cuando está off / entre ciclos (segundos).
_SCHEDULER_POLL_S = 5.0


@dataclass(frozen=True, slots=True)
class BackupInfo:
    filename: str
    path: Path
    bytes: int
    mtime_utc: str
    sha256: str | None = None


def backups_dir(session: WorkbenchSession) -> Path:
    """``session/backups/`` (creado on-demand)."""
    dest = Path(session.root) / BACKUPS_DIRNAME
    dest.mkdir(parents=True, exist_ok=True)
    return dest.resolve()


def _list_backup_zips(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    zips = [
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() == ".zip" and p.name.startswith("session_")
    ]
    zips.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return zips


def rotate_backups(directory: Path, *, max_keep: int = MAX_BACKUPS) -> list[Path]:
    """Elimina ZIPs más viejos dejando como máximo ``max_keep`` (más recientes)."""
    if max_keep < 1:
        raise ValidationError("max_keep debe ser >= 1")
    kept: list[Path] = []
    removed: list[Path] = []
    for idx, path in enumerate(_list_backup_zips(directory)):
        if idx < max_keep:
            kept.append(path)
            continue
        # Sidecar .sha256 si existe.
        side = Path(str(path) + ".sha256")
        path.unlink(missing_ok=True)
        side.unlink(missing_ok=True)
        removed.append(path)
    return removed


def run_auto_backup(session: WorkbenchSession) -> SessionExportResult:
    """Trigger manual: export ZIP → ``session/backups/`` + rotación max 5.

    Reutiliza ``export_session`` (allowlist + zip-slip fail-closed · sin secretos).
    """
    if not LIVE_BLOCKED:
        raise ValidationError("LIVE_BLOCKED debe ser True; auto-backup aborta")
    session.ensure_layout()
    dest = backups_dir(session)
    result = export_session(session, dest_dir=dest)
    rotate_backups(dest, max_keep=MAX_BACKUPS)
    return result


def list_backups(session: WorkbenchSession) -> dict[str, Any]:
    """Lista ZIPs en ``session/backups/`` (más recientes primero)."""
    session.ensure_layout()
    dest = backups_dir(session)
    items: list[dict[str, Any]] = []
    for path in _list_backup_zips(dest):
        st = path.stat()
        mtime = datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat()
        sha_path = Path(str(path) + ".sha256")
        sha: str | None = None
        if sha_path.is_file():
            try:
                first = sha_path.read_text(encoding="utf-8").strip().split()[0]
                sha = first or None
            except (OSError, UnicodeDecodeError, IndexError):
                sha = None
        items.append(
            {
                "filename": path.name,
                "path": str(path),
                "bytes": int(st.st_size),
                "mtime_utc": mtime,
                "sha256": sha,
            }
        )
    minutes = DEFAULT_AUTO_BACKUP_MINUTES
    try:
        settings = load_settings(session.settings_path)
        minutes = parse_auto_backup_minutes(settings.get("auto_backup_minutes"))
    except ValidationError:
        minutes = DEFAULT_AUTO_BACKUP_MINUTES
    return {
        "ok": True,
        "kind": "backups",
        "session_id": session.session_id,
        "backups_dir": str(dest),
        "count": len(items),
        "max_keep": MAX_BACKUPS,
        "auto_backup_minutes": minutes,
        "auto_backup_enabled": minutes > 0,
        "backups": items,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
        "banner": "session auto-backup research-safe — ZIP allowlist · rotación max 5 · sin LIVE",
    }


class AutoBackupScheduler:
    """Thread daemon: si ``auto_backup_minutes`` > 0, exporta periódicamente."""

    def __init__(self, state: Any) -> None:
        self._state = state
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._last_backup_monotonic: float | None = None
        self._last_error: str | None = None
        self._runs = 0

    @property
    def runs(self) -> int:
        return self._runs

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def alive(self) -> bool:
        t = self._thread
        return t is not None and t.is_alive()

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._loop,
                name="quantlab-auto-backup",
                daemon=True,
            )
            self._thread.start()

    def stop(self, *, join_timeout: float = 2.0) -> None:
        self._stop.set()
        thread: threading.Thread | None
        with self._lock:
            thread = self._thread
            self._thread = None
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=join_timeout)

    def notify_settings_changed(self) -> None:
        """Despierta el poll tras PUT settings (no bloquea)."""
        # El loop ya hace poll corto; reset de last permite backup inmediato
        # si el usuario acaba de activar el intervalo.
        self._last_backup_monotonic = None

    def _read_minutes(self) -> int:
        session = getattr(self._state, "session", None)
        if session is None:
            return 0
        try:
            settings = load_settings(session.settings_path)
            return parse_auto_backup_minutes(settings.get("auto_backup_minutes"))
        except Exception:  # noqa: BLE001 — fail-soft en background
            return 0

    def _loop(self) -> None:
        while not self._stop.is_set():
            minutes = self._read_minutes()
            if minutes <= 0:
                self._stop.wait(_SCHEDULER_POLL_S)
                continue
            interval_s = float(minutes) * 60.0
            now = time.monotonic()
            due = (
                self._last_backup_monotonic is None
                or (now - self._last_backup_monotonic) >= interval_s
            )
            if due:
                try:
                    session = self._state.ensure_session()
                    run_auto_backup(session)
                    self._last_backup_monotonic = time.monotonic()
                    self._runs += 1
                    self._last_error = None
                except Exception as exc:  # noqa: BLE001 — no tumbar el servidor
                    self._last_error = str(exc)
                    logger.warning("auto-backup falló: %s", exc)
                    self._last_backup_monotonic = time.monotonic()
            # Sleep corto para poder stop/react rápido.
            self._stop.wait(min(_SCHEDULER_POLL_S, interval_s))


def ensure_auto_backup_scheduler(state: Any) -> AutoBackupScheduler:
    """Adjunta scheduler al state (idempotente) y lo arranca."""
    existing = getattr(state, "auto_backup_scheduler", None)
    if isinstance(existing, AutoBackupScheduler):
        existing.start()
        return existing
    sched = AutoBackupScheduler(state)
    state.auto_backup_scheduler = sched
    sched.start()
    return sched


def stop_auto_backup_scheduler(state: Any) -> None:
    existing = getattr(state, "auto_backup_scheduler", None)
    if isinstance(existing, AutoBackupScheduler):
        existing.stop()
