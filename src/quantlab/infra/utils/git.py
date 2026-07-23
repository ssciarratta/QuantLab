"""Git utilities for reproducibility."""

from __future__ import annotations

import subprocess


def get_git_commit() -> str:
    """Get the current git commit hash.

    Returns 'unknown' if git is not available or the directory
    is not a git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    except FileNotFoundError:
        return "unknown"
    except subprocess.TimeoutExpired:
        return "unknown"
