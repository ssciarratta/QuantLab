"""Singleton launcher — cierra este.bat / workbench previos al arrancar."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.workbench.instance_lock import (
    _find_pid_listening,
    clear_lock,
    default_lock_path,
    pid_is_alive,
    port_in_use,
    read_lock_pid,
    terminate_pid,
    wait_port_free,
)
from quantlab.workbench.session import DEFAULT_SESSION_PARENT

DEFAULT_LAUNCHER_LOCK_NAME = "launcher.pid"
_CMD_MARKERS = (
    "arrancar_workbench.py",
    "quantlab.workbench.launch",
    "quantlab-workbench",
)


@dataclass(frozen=True, slots=True)
class LauncherLockRecord:
    launcher_pid: int
    parent_pid: int | None
    started_at: str


def default_launcher_lock_path() -> Path:
    return (DEFAULT_SESSION_PARENT.parent / DEFAULT_LAUNCHER_LOCK_NAME).resolve()


def _get_parent_pid(pid: int | None = None) -> int | None:
    use = int(pid if pid is not None else os.getpid())
    if sys.platform == "win32":
        try:
            import subprocess

            out = subprocess.run(
                ["wmic", "process", "where", f"ProcessId={use}", "get", "ParentProcessId"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            for line in (out.stdout or "").splitlines():
                token = line.strip()
                if token.isdigit():
                    val = int(token)
                    if val != use and val > 0:
                        return val
        except (OSError, subprocess.TimeoutExpired, ValueError):
            return None
        return None
    try:
        return os.getppid()
    except OSError:
        return None


def read_launcher_lock(lock_path: Path | None = None) -> LauncherLockRecord | None:
    path = (lock_path or default_launcher_lock_path()).resolve()
    try:
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError:
        return None
    if not lines:
        return None
    try:
        launcher_pid = int(lines[0])
    except ValueError:
        return None
    parent_pid: int | None = None
    started_at = ""
    if len(lines) > 1 and lines[1].isdigit():
        parent_pid = int(lines[1])
    if len(lines) > 2:
        started_at = lines[2]
    return LauncherLockRecord(
        launcher_pid=launcher_pid,
        parent_pid=parent_pid,
        started_at=started_at,
    )


def write_launcher_lock(
    lock_path: Path | None = None,
    *,
    launcher_pid: int | None = None,
    parent_pid: int | None = None,
) -> Path:
    path = (lock_path or default_launcher_lock_path()).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    lp = int(launcher_pid if launcher_pid is not None else os.getpid())
    pp = parent_pid if parent_pid is not None else _get_parent_pid(lp)
    started = datetime.now(UTC).isoformat()
    body = f"{lp}\n{pp or ''}\n{started}\n"
    path.write_text(body, encoding="utf-8")
    return path


def clear_launcher_lock(lock_path: Path | None = None, *, only_if_pid: int | None = None) -> None:
    path = (lock_path or default_launcher_lock_path()).resolve()
    if only_if_pid is not None:
        rec = read_launcher_lock(path)
        if rec is not None and rec.launcher_pid != only_if_pid:
            return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _kill_pid_if_alive(pid: int, killed: list[int]) -> None:
    if pid <= 0 or pid == os.getpid():
        return
    if not pid_is_alive(pid):
        return
    if terminate_pid(pid, force=True):
        killed.append(pid)


def _sweep_quantlab_cmdline(*, exclude: set[int]) -> list[int]:
    """Mata procesos QuantLab launcher/workbench ajenos al PID actual."""
    if sys.platform != "win32":
        return []
    import subprocess

    killed: list[int] = []
    try:
        out = subprocess.run(
            ["wmic", "process", "get", "ProcessId,CommandLine"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        return killed
    text = out.stdout or ""
    for line in text.splitlines():
        if not any(marker in line for marker in _CMD_MARKERS):
            continue
        parts = line.rsplit(None, 1)
        if len(parts) != 2 or not parts[1].isdigit():
            continue
        pid = int(parts[1])
        if pid in exclude or pid in killed:
            continue
        _kill_pid_if_alive(pid, killed)
    return killed


def claim_launcher_singleton(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    lock_path: Path | None = None,
) -> dict[str, Any]:
    """Cierra ventanas este.bat previas, launcher Python y workbench en :port."""
    path = (lock_path or default_launcher_lock_path()).resolve()
    killed: list[int] = []
    me = os.getpid()
    exclude = {me}

    prev = read_launcher_lock(path)
    if prev is not None:
        exclude.add(prev.launcher_pid)
        if prev.parent_pid is not None:
            exclude.add(prev.parent_pid)
        current_parent = _get_parent_pid(me)
        # Cerrar ventana cmd del este.bat anterior (no la ventana actual).
        if (
            prev.parent_pid is not None
            and prev.parent_pid != current_parent
            and prev.parent_pid != me
        ):
            _kill_pid_if_alive(prev.parent_pid, killed)
        if prev.launcher_pid != me and pid_is_alive(prev.launcher_pid):
            _kill_pid_if_alive(prev.launcher_pid, killed)
        time.sleep(0.3)

    wb_path = default_lock_path()
    wb_pid = read_lock_pid(wb_path)
    if wb_pid is not None:
        _kill_pid_if_alive(wb_pid, killed)
    clear_lock(wb_path)

    for _ in range(3):
        occupant = _find_pid_listening(port)
        if occupant is None or occupant in exclude or occupant in killed:
            break
        _kill_pid_if_alive(occupant, killed)
        wait_port_free(host, port, timeout_s=4.0)
        time.sleep(0.2)

    swept = _sweep_quantlab_cmdline(exclude=exclude | set(killed) | {me})
    killed.extend(p for p in swept if p not in killed)

    if killed:
        wait_port_free(host, port, timeout_s=6.0)
        time.sleep(0.4)

    write_launcher_lock(path, launcher_pid=me, parent_pid=_get_parent_pid(me))
    return {
        "ok": True,
        "launcher_pid": me,
        "parent_pid": _get_parent_pid(me),
        "lock_path": str(path),
        "killed_pids": killed,
        "port": int(port),
        "port_free": not port_in_use(host, port),
    }


__all__ = [
    "LauncherLockRecord",
    "claim_launcher_singleton",
    "clear_launcher_lock",
    "default_launcher_lock_path",
    "read_launcher_lock",
    "write_launcher_lock",
]
