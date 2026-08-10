"""Bootstrap idempotente de Kronos (vendor + deps torch/pandas).

Uso:
  python scripts/ensure_kronos.py          # instala solo si falta algo
  python scripts/ensure_kronos.py --check  # exit 0 si OK, 1 si falta
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VENDOR = REPO / "third_party" / "kronos"
VENDOR_GIT = "https://github.com/shiyu-coder/Kronos.git"


def _python() -> Path | None:
    for rel in (".venv/Scripts/python.exe", "venv/Scripts/python.exe"):
        exe = REPO / rel
        if exe.is_file():
            return exe
    return None


def _site_packages(py: Path) -> Path:
    return py.resolve().parent.parent / "Lib" / "site-packages"


def _fast_deps_ok(py: Path) -> bool:
    """Chequeo rápido (sin importar torch) para no demorar cada arranque."""
    if not VENDOR.is_dir():
        return False
    site = _site_packages(py)
    return any(site.glob("torch-*.dist-info")) and any(site.glob("pandas-*.dist-info"))


def _deps_ok(py: Path) -> bool:
    if not _fast_deps_ok(py):
        return False
    proc = subprocess.run(
        [str(py), "-c", "import torch, pandas"],  # noqa: S607
        cwd=str(REPO),
        capture_output=True,
        text=True,
        errors="replace",
    )
    return proc.returncode == 0


def _clone_vendor() -> None:
    VENDOR.parent.mkdir(parents=True, exist_ok=True)
    print(f"Clonando Kronos en {VENDOR} …")
    subprocess.run(
        ["git", "clone", "--depth", "1", VENDOR_GIT, str(VENDOR)],
        cwd=str(REPO),
        check=True,
    )


def _uv_sync() -> None:
    print("Instalando deps Kronos (torch, pandas, …) — puede tardar varios minutos …")
    subprocess.run(
        ["uv", "sync", "--extra", "kronos", "--extra", "dev"],
        cwd=str(REPO),
        check=True,
    )


def _warm_model(py: Path) -> None:
    print("Descargando modelo Kronos (solo la primera vez, puede tardar) …")
    env = dict(__import__("os").environ)
    env["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    env["TQDM_ASCII"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    code = (
        "from quantlab.research.alpha.kronos import KronosConfig, get_forecast_engine; "
        "eng = get_forecast_engine(KronosConfig(enabled=True)); "
        "h = eng.health(); "
        "assert h.get('ok'), h; "
        "print('Modelo Kronos cargado:', h.get('model'))"
    )
    subprocess.run([str(py), "-c", code], cwd=str(REPO), env=env, check=True)


def ensure_kronos(*, install: bool = True) -> bool:
    changed = False
    if not VENDOR.is_dir():
        if not install:
            print("Falta vendor:", VENDOR)
            return False
        _clone_vendor()
        changed = True

    py = _python()
    if py is None:
        if not install:
            print("Falta .venv")
            return False
        print("Creando entorno con uv sync …")
        _uv_sync()
        py = _python()
        if py is None:
            print("ERROR: no hay .venv tras uv sync")
            return False
        changed = True

    if not _fast_deps_ok(py):
        if not install:
            print("Faltan deps Kronos (torch/pandas)")
            return False
        _uv_sync()
        changed = True
        py = _python() or py

    if not _fast_deps_ok(py):
        print("ERROR: Kronos sigue sin deps tras uv sync")
        return False

    if changed and install:
        try:
            _warm_model(py)
        except subprocess.CalledProcessError as exc:
            print("Aviso: modelo Kronos se descargará en el primer escaneo.", file=sys.stderr)
            print(f"  ({exc})", file=sys.stderr)

    if changed:
        print("OK: Kronos listo (vendor + deps).")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Kronos para Alpha Scanner")
    parser.add_argument("--check", action="store_true", help="solo verificar, no instalar")
    parser.add_argument("--quiet", action="store_true", help="sin mensajes si ya está OK")
    args = parser.parse_args()
    py = _python()
    if args.check and py and _fast_deps_ok(py) and VENDOR.is_dir():
        if not args.quiet:
            print("OK: Kronos operativo.")
        return 0
    ok = ensure_kronos(install=not args.check)
    if ok and args.quiet and not args.check:
        pass
    elif ok and args.check:
        print("OK: Kronos operativo.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
