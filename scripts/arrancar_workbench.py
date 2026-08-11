"""Launcher Windows/CLI: carga .env + arranca Workbench + abre browser.

Uso:
  .venv\\Scripts\\python.exe scripts\\arrancar_workbench.py
  o doble-clic en este.bat

Por defecto REINICIA el proceso en :8765 para cargar código/.env nuevos.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8765"
PORT = 8765


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        print("Aviso: no hay .env — chat offline (FakeProvider).")
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            os.environ[key] = val
    print("OK: .env cargado.")


def server_alive(url: str = URL, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return int(getattr(resp, "status", 200) or 200) == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def kill_port(port: int = PORT) -> None:
    """Mata el proceso que escucha en TCP :port (Windows)."""
    from quantlab.workbench.launcher_singleton import claim_launcher_singleton

    claim = claim_launcher_singleton(host="127.0.0.1", port=port)
    if claim.get("killed_pids"):
        print(f"Reiniciando: instancias previas cerradas pids={claim['killed_pids']}")


def _ensure_pythonpath() -> None:
    src = str(REPO / "src")
    existing = os.environ.get("PYTHONPATH", "")
    parts = [p for p in existing.split(os.pathsep) if p]
    if src not in parts:
        os.environ["PYTHONPATH"] = src + (os.pathsep + existing if existing else "")


def workbench_cmd() -> list[str]:
    args = ["--no-browser", "--port", str(PORT)]
    py = REPO / ".venv" / "Scripts" / "python.exe"
    if py.is_file():
        return [str(py), "-m", "quantlab.workbench.launch", *args]
    return ["uv", "run", "--no-sync", "quantlab-workbench", *args]


def print_llm_status() -> None:
    key = os.environ.get("QUANTLAB_LLM_API_KEY", "DISABLED").strip()
    provider = os.environ.get("QUANTLAB_LLM_PROVIDER", "gemini").strip() or "gemini"
    if key in {"", "DISABLED", "0", "false", "FALSE", "none", "NONE"}:
        print("Chat IA: OFFLINE (FakeProvider)")
        print("  Tip: ejecutá configurar_chat_llm.bat o editá .env")
    else:
        print(f"Chat IA: ON  provider={provider}  (key oculta)")
        print("  Si en el chat ves provider=fake, el servidor viejo no cargo .env -> reinicia.")


def main() -> int:
    os.chdir(REPO)
    _ensure_pythonpath()
    from quantlab.workbench.launcher_singleton import (
        claim_launcher_singleton,
        clear_launcher_lock,
    )

    print("QuantLab Workbench")
    print("Repo:", REPO)
    print("URL:", URL)

    claim = claim_launcher_singleton(host="127.0.0.1", port=PORT)
    if claim.get("killed_pids"):
        print(
            "Instancias previas cerradas (ventanas este.bat / workbench): "
            + ", ".join(str(p) for p in claim["killed_pids"])
        )
    elif not claim.get("port_free"):
        print("Aviso: puerto :8765 aún ocupado; reintentando liberar…")
        kill_port(PORT)

    load_dotenv(REPO / ".env")
    # Post-.env: forzar UTF-8 (Windows ASCII + tqdm █ tumba Alpha Scanner).
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    os.environ["TQDM_ASCII"] = "1"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    print_llm_status()

    # Asegurar :8765 libre (claim_launcher_singleton ya mató ocupantes).
    if server_alive():
        print("\nWorkbench previo aún respondía — reinicio con .env actual.")
        kill_port(PORT)
        for _ in range(20):
            if not server_alive():
                break
            time.sleep(0.2)

    cmd = workbench_cmd()
    print("Arrancando:", " ".join(cmd))
    print("Dejá esta ventana abierta. Ctrl+C para apagar.\n")

    proc = subprocess.Popen(cmd, cwd=str(REPO), env=os.environ.copy())
    for _ in range(60):
        time.sleep(0.25)
        if server_alive():
            break
    if not server_alive():
        print("ERROR: el workbench no respondió en :8765")
        proc.terminate()
        return 1

    webbrowser.open(URL)
    print("Navegador abierto ->", URL)
    print("Proba Chat IA: quiero correr alpha scanner en binance como hago?")
    print("Abajo del chat deberias ver provider=llm (no fake).\n")
    try:
        return int(proc.wait())
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("\nWorkbench detenido.")
        return 0
    finally:
        clear_launcher_lock(only_if_pid=os.getpid())


if __name__ == "__main__":
    raise SystemExit(main())
