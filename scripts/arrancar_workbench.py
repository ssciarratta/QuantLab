"""Launcher Windows/CLI: carga .env + arranca Workbench + abre browser.

Uso:
  .venv\\Scripts\\python.exe scripts\\arrancar_workbench.py
  o doble-clic en arrancar_quantlab.bat

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
    if sys.platform != "win32":
        return
    try:
        out = subprocess.check_output(
            ["netstat", "-ano"],
            text=True,
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.CalledProcessError):
        return
    pids: set[str] = set()
    needle = f":{port}"
    for line in out.splitlines():
        if "LISTENING" not in line:
            continue
        if needle not in line:
            continue
        parts = line.split()
        if not parts:
            continue
        pid = parts[-1]
        if pid.isdigit() and pid != "0":
            pids.add(pid)
    for pid in pids:
        print(f"Reiniciando: matando PID {pid} en :{port}")
        subprocess.run(
            ["taskkill", "/F", "/PID", pid],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    if pids:
        time.sleep(0.8)


def workbench_cmd() -> list[str]:
    exe = REPO / ".venv" / "Scripts" / "quantlab-workbench.exe"
    if exe.is_file():
        return [str(exe), "--no-browser", "--port", str(PORT)]
    py = REPO / ".venv" / "Scripts" / "python.exe"
    if py.is_file():
        return [str(py), "-m", "quantlab.workbench.launch", "--no-browser", "--port", str(PORT)]
    return ["uv", "run", "quantlab-workbench", "--no-browser", "--port", str(PORT)]


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
    print("QuantLab Workbench")
    print("Repo:", REPO)
    print("URL:", URL)
    load_dotenv(REPO / ".env")
    print_llm_status()

    # Siempre reiniciar :8765 para cargar código + .env nuevos
    if server_alive():
        print("\nHay un workbench viejo en :8765 — lo reinicio con .env actual.")
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


if __name__ == "__main__":
    raise SystemExit(main())
