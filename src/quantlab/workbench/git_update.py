"""Estado de versión local vs GitHub + apply ``git pull`` (loopback / research-safe)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab import __version__
from quantlab.execution.live_gate import LIVE_BLOCKED

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VERSION_RE = re.compile(r'(?m)^version\s*=\s*["\']([^"\']+)["\']')
_DEFAULT_GH_OWNER = "ssciarratta"
_DEFAULT_GH_REPO = "QuantLab"
_DEFAULT_BRANCH = "main"
_HTTP_TIMEOUT_S = 12.0


def repo_root() -> Path:
    return _REPO_ROOT


def parse_pyproject_version(text: str) -> str | None:
    m = _VERSION_RE.search(text)
    return m.group(1).strip() if m else None


def local_pyproject_version(root: Path | None = None) -> str:
    path = (root or _REPO_ROOT) / "pyproject.toml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return __version__
    return parse_pyproject_version(text) or __version__


def _run_git(
    args: list[str],
    *,
    cwd: Path,
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def local_git_head_info(root: Path | None = None) -> dict[str, Any]:
    """Commit tip local + fecha de autor."""
    cwd = root or _REPO_ROOT
    out: dict[str, Any] = {
        "commit": None,
        "committed_at": None,
        "subject": None,
        "branch": None,
    }
    try:
        head = _run_git(["rev-parse", "HEAD"], cwd=cwd, timeout=8)
        if head.returncode == 0:
            out["commit"] = head.stdout.strip()[:12]
        branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, timeout=8)
        if branch.returncode == 0:
            out["branch"] = branch.stdout.strip()
        meta = _run_git(
            ["log", "-1", "--format=%cI%n%s"],
            cwd=cwd,
            timeout=8,
        )
        if meta.returncode == 0:
            lines = meta.stdout.strip().splitlines()
            if lines:
                out["committed_at"] = lines[0].strip()
            if len(lines) > 1:
                out["subject"] = lines[1].strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return out


def resolve_github_slug(root: Path | None = None) -> tuple[str, str, str]:
    """(owner, repo, branch) desde remote origin o defaults."""
    cwd = root or _REPO_ROOT
    owner, repo, branch = _DEFAULT_GH_OWNER, _DEFAULT_GH_REPO, _DEFAULT_BRANCH
    try:
        remote = _run_git(["remote", "get-url", "origin"], cwd=cwd, timeout=8)
        if remote.returncode == 0:
            url = remote.stdout.strip()
            m = re.search(r"github\.com[:/](?P<o>[^/]+)/(?P<r>[^/.]+)", url)
            if m:
                owner, repo = m.group("o"), m.group("r")
        br = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, timeout=8)
        if br.returncode == 0 and br.stdout.strip() not in ("", "HEAD"):
            # Preferir tip de main en GitHub para “última subida”
            branch = _DEFAULT_BRANCH
    except (OSError, subprocess.TimeoutExpired):
        pass
    return owner, repo, branch


def fetch_github_tip(
    *,
    owner: str | None = None,
    repo: str | None = None,
    branch: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Consulta tip público de GitHub (versión pyproject + fecha commit)."""
    o, r, b = resolve_github_slug(root)
    owner = owner or o
    repo = repo or r
    branch = branch or b
    result: dict[str, Any] = {
        "ok": False,
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "version": None,
        "committed_at": None,
        "commit": None,
        "source": "github",
        "error": None,
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"QuantLab-Workbench/{__version__}",
    }
    token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 1) Commit tip
    commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
    try:
        req = urllib.request.Request(commit_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_S) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        sha = str(payload.get("sha") or "")
        result["commit"] = sha[:12] if sha else None
        commit_obj = payload.get("commit") if isinstance(payload.get("commit"), dict) else {}
        committer = commit_obj.get("committer") if isinstance(commit_obj, dict) else {}
        if isinstance(committer, dict):
            result["committed_at"] = committer.get("date")
        result["ok"] = True
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        json.JSONDecodeError,
        OSError,
    ) as exc:
        result["error"] = f"commit: {exc}"
        return result

    # 2) pyproject version en ese branch
    raw_url = (
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/pyproject.toml"
    )
    try:
        req = urllib.request.Request(
            raw_url,
            headers={"User-Agent": headers["User-Agent"]},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_S) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        ver = parse_pyproject_version(text)
        if ver:
            result["version"] = ver
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        result["error"] = (result.get("error") or "") + f" | pyproject: {exc}"
    return result


def working_tree_last_modified_iso(root: Path | None = None) -> str | None:
    """ISO-8601 del archivo más reciente bajo el árbol de código (sin __pycache__).

    Así el banner refleja ediciones locales aunque aún no haya commit.
    """
    cwd = root or _REPO_ROOT
    newest: float | None = None
    scan_roots: list[Path] = [
        cwd / "src" / "quantlab",
        cwd / "pyproject.toml",
        cwd / "RESUMEN_PROYECTO.txt",
    ]
    skip_parts = {"__pycache__", ".pyc", ".git", ".venv", "venv", "node_modules"}

    def _consider(path: Path) -> None:
        nonlocal newest
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return
        if newest is None or mtime > newest:
            newest = mtime

    for base in scan_roots:
        if base.is_file():
            _consider(base)
            continue
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in skip_parts]
            for name in filenames:
                if name.endswith(".pyc") or name.endswith(".pyo"):
                    continue
                _consider(Path(dirpath) / name)

    if newest is None:
        return None
    return datetime.fromtimestamp(newest, tz=UTC).isoformat()


def build_update_status(*, root: Path | None = None, fetch_remote: bool = True) -> dict[str, Any]:
    """Payload para banner: versión local, GitHub, última modificación."""
    cwd = root or _REPO_ROOT
    local_ver = local_pyproject_version(cwd)
    local_git = local_git_head_info(cwd)
    remote: dict[str, Any] | None = None
    if fetch_remote:
        remote = fetch_github_tip(root=cwd)

    remote_ver = remote.get("version") if remote else None
    update_available = bool(
        remote
        and remote.get("ok")
        and remote_ver
        and remote_ver != local_ver
    )
    # También si el commit tip difiere aunque la versión de paquete sea igual
    if (
        not update_available
        and remote
        and remote.get("ok")
        and remote.get("commit")
        and local_git.get("commit")
        and remote["commit"] != local_git["commit"]
    ):
        update_available = True

    last_mod = local_git.get("committed_at") or None
    last_mod_source = "local_git"
    if remote and remote.get("committed_at") and (
        not last_mod or (remote.get("ok") and update_available)
    ):
        # Mostrar la más reciente entre local y GitHub tip
        last_mod = _max_iso(last_mod, remote.get("committed_at"))
        last_mod_source = "max(local,github)"

    tree_mod = working_tree_last_modified_iso(cwd)
    if tree_mod:
        prev = last_mod
        last_mod = _max_iso(last_mod, tree_mod)
        if last_mod == tree_mod and tree_mod != prev:
            last_mod_source = "working_tree"

    return {
        "ok": True,
        "kind": "update_status",
        "local_version": local_ver,
        "package_version": __version__,
        "github_version": remote_ver if remote and remote.get("ok") else None,
        "update_available": update_available,
        "last_modified_at": last_mod,
        "last_modified_source": last_mod_source,
        "last_modified_display": format_es_ar(last_mod),
        "local_git": local_git,
        "github": remote,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
        "needs_restart_after_update": True,
    }


def apply_git_update(
    *,
    root: Path | None = None,
    remote: str = "origin",
    branch: str = _DEFAULT_BRANCH,
) -> dict[str, Any]:
    """``git fetch`` + ``git pull --ff-only`` desde GitHub. Sin flip LIVE."""
    cwd = root or _REPO_ROOT
    if not LIVE_BLOCKED:
        return {
            "ok": False,
            "error": "update bloqueado: LIVE_BLOCKED debe ser True",
            "live_blocked": False,
        }
    steps: list[dict[str, Any]] = []

    fetch = _run_git(["fetch", remote, branch], cwd=cwd, timeout=120)
    steps.append(
        {
            "cmd": f"git fetch {remote} {branch}",
            "returncode": fetch.returncode,
            "stdout": (fetch.stdout or "")[-2000:],
            "stderr": (fetch.stderr or "")[-2000:],
        }
    )
    if fetch.returncode != 0:
        return {
            "ok": False,
            "error": "git fetch falló",
            "steps": steps,
            "live_blocked": True,
            "needs_restart": False,
        }

    pull = _run_git(["pull", "--ff-only", remote, branch], cwd=cwd, timeout=120)
    steps.append(
        {
            "cmd": f"git pull --ff-only {remote} {branch}",
            "returncode": pull.returncode,
            "stdout": (pull.stdout or "")[-2000:],
            "stderr": (pull.stderr or "")[-2000:],
        }
    )
    if pull.returncode != 0:
        return {
            "ok": False,
            "error": "git pull --ff-only falló (¿cambios locales?)",
            "steps": steps,
            "live_blocked": True,
            "needs_restart": False,
        }

    sync_note: str | None = None
    try:
        sync = subprocess.run(
            ["uv", "sync", "--extra", "dev"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        steps.append(
            {
                "cmd": "uv sync --extra dev",
                "returncode": sync.returncode,
                "stdout": (sync.stdout or "")[-1500:],
                "stderr": (sync.stderr or "")[-1500:],
            }
        )
        if sync.returncode != 0:
            sync_note = "uv sync falló; el código se actualizó — revisá deps a mano"
    except (OSError, subprocess.TimeoutExpired) as exc:
        sync_note = f"uv sync omitido: {exc}"

    status = build_update_status(root=cwd, fetch_remote=True)
    return {
        "ok": True,
        "message": "Actualización aplicada. Reiniciá QuantLab para cargar el código nuevo.",
        "steps": steps,
        "sync_note": sync_note,
        "needs_restart": True,
        "status": status,
        "live_blocked": LIVE_BLOCKED is True,
        "live_routing": False,
        "research_safe": True,
    }


def format_es_ar(iso: str | None) -> str:
    """Formatea ISO-8601 a ``dd/mm/yyyy HH:MM`` local-ish (muestra UTC si no parsea tz)."""
    if not iso or not isinstance(iso, str):
        return "—"
    text = iso.strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        local = dt.astimezone()
        return local.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso[:16]


def _max_iso(a: str | None, b: str | None) -> str | None:
    if not a:
        return b
    if not b:
        return a
    try:
        da = datetime.fromisoformat(a.replace("Z", "+00:00"))
        db = datetime.fromisoformat(b.replace("Z", "+00:00"))
        return a if da >= db else b
    except ValueError:
        return b or a
