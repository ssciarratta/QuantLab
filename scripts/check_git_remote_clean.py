#!/usr/bin/env python3
"""Falla si algún remote Git contiene un token o userinfo embebido en la URL."""

from __future__ import annotations

import re
import subprocess
import sys

_TOKEN_RE = re.compile(
    r"(ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|glpat-)[A-Za-z0-9_]{20,}",
    re.IGNORECASE,
)
# https://user:pass@host o https://token@host
_USERINFO_RE = re.compile(r"https?://[^/\s:]+:[^/\s]+@", re.IGNORECASE)


def remote_has_embedded_secret(line: str) -> bool:
    return bool(_TOKEN_RE.search(line) or _USERINFO_RE.search(line))


def main() -> int:
    result = subprocess.run(
        ["git", "remote", "-v"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: no se pudo leer git remote", file=sys.stderr)
        return 2
    bad = False
    for line in result.stdout.splitlines():
        if remote_has_embedded_secret(line):
            name = line.split()[0] if line.split() else "?"
            print(f"FAIL: remote '{name}' contiene credencial embebida", file=sys.stderr)
            bad = True
    if bad:
        print(
            "Acción: git remote set-url origin https://github.com/<user>/<repo>.git "
            "y revocar el token en GitHub Settings.",
            file=sys.stderr,
        )
        return 1
    print("OK: remotes sin tokens embebidos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
