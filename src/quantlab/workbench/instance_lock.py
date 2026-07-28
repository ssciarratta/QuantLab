"""Singleton Workbench — un solo proceso por puerto (mata instancia previa)."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from quantlab.workbench.session import DEFAULT_SESSION_PARENT

DEFAULT_LOCK_NAME = "workbench.pid"
_WAIT_PORT_FREE_S = 8.0
_POLL_S = 0.2


def default_lock_path() -> Path:
    """Lockfile junto a las sesiones: ``data/runtime/workbench.pid``."""
    return (DEFAULT_SESSION_PARENT.parent / DEFAULT_LOCK_NAME).resolve()


def pid_is_alive(pid: int) -> bool:
    """True si el PID existe (best-effort cross-platform)."""
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if sys.platform == "win32":
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        text = (out.stdout or "") + (out.stderr or "")
        return str(pid) in text
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def terminate_pid(pid: int, *, force: bool = True) -> bool:
    """Intenta terminar ``pid``. True si se envió señal / taskkill OK."""
    if pid <= 0 or pid == os.getpid():
        return False
    if sys.platform == "win32":
        args = ["taskkill", "/PID", str(pid)]
        if force:
            args.append("/F")
        try:
            completed = subprocess.run(
                args, capture_output=True, text=True, timeout=10, check=False
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return completed.returncode == 0
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    if force:
        time.sleep(0.4)
        if pid_is_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                return False
    return True


def port_in_use(host: str, port: int, *, timeout_s: float = 0.35) -> bool:
    """True si algo acepta TCP en host:port."""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_s):
            return True
    except OSError:
        return False


def read_lock_pid(lock_path: Path) -> int | None:
    """Lee PID del lockfile; None si inválido/ausente."""
    try:
        raw = lock_path.read_text(encoding="utf-8").strip().splitlines()
    except OSError:
        return None
    if not raw:
        return None
    try:
        pid = int(raw[0].strip())
    except ValueError:
        return None
    return pid if pid > 0 else None


def write_lock(lock_path: Path, pid: int | None = None) -> Path:
    """Escribe lockfile con PID actual (+ meta mínima)."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    use_pid = int(pid if pid is not None else os.getpid())
    lock_path.write_text(f"{use_pid}\n", encoding="utf-8")
    return lock_path


def clear_lock(lock_path: Path, *, only_if_pid: int | None = None) -> None:
    """Borra lockfile; si ``only_if_pid`` no coincide, no toca."""
    if only_if_pid is not None:
        current = read_lock_pid(lock_path)
        if current is not None and current != only_if_pid:
            return
    try:
        lock_path.unlink(missing_ok=True)
    except OSError:
        pass


def wait_port_free(host: str, port: int, *, timeout_s: float = _WAIT_PORT_FREE_S) -> bool:
    """Espera hasta que el puerto quede libre."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not port_in_use(host, port):
            return True
        time.sleep(_POLL_S)
    return not port_in_use(host, port)


def claim_singleton(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    lock_path: Path | None = None,
) -> dict[str, Any]:
    """Mata instancia previa (PID lock y/o ocupante del puerto) y escribe lock.

    Cada arranque de QuantLab deja una sola sesión HTTP viva en el puerto.
    """
    path = (lock_path or default_lock_path()).resolve()
    killed: list[int] = []
    prev = read_lock_pid(path)
    if prev is not None and prev != os.getpid() and pid_is_alive(prev):
        if terminate_pid(prev, force=True):
            killed.append(prev)
        wait_port_free(host, port)

    # Si el puerto sigue ocupado (lock stale / otro proceso), intentar hallar PID (Windows).
    if port_in_use(host, port):
        occupant = _find_pid_listening(port)
        if occupant is not None and occupant != os.getpid() and occupant not in killed:
            if terminate_pid(occupant, force=True):
                killed.append(occupant)
            wait_port_free(host, port)

    write_lock(path, os.getpid())
    return {
        "ok": True,
        "pid": os.getpid(),
        "lock_path": str(path),
        "killed_pids": killed,
        "port": int(port),
        "host": host,
        "port_free": not port_in_use(host, port),
    }


def _find_pid_listening(port: int) -> int | None:
    """Best-effort: PID que escucha ``port`` (Windows netstat / Linux ss)."""
    port = int(port)
    if sys.platform == "win32":
        try:
            out = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        needle = f":{port}"
        for line in (out.stdout or "").splitlines():
            if "LISTENING" not in line.upper() and "ESCUCHANDO" not in line.upper():
                # Algunas locales usan LISTENING; aceptar también si aparece el puerto.
                if "LISTEN" not in line.upper():
                    continue
            if needle not in line:
                continue
            parts = line.split()
            if not parts:
                continue
            try:
                return int(parts[-1])
            except ValueError:
                continue
        return None
    # Linux/mac: ss -ltnp o lsof
    for cmd in (
        ["ss", "-ltnp", f"sport = :{port}"],
        ["lsof", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
    ):
        try:
            out = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5, check=False
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        text = out.stdout or ""
        if cmd[0] == "lsof":
            for line in text.splitlines():
                line = line.strip()
                if line.isdigit():
                    return int(line)
            continue
        # ss: users:(("python",pid=1234,fd=3))
        import re

        m = re.search(r"pid=(\d+)", text)
        if m:
            return int(m.group(1))
    return None
