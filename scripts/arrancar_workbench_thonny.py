"""Arrancar QuantLab Workbench desde Thonny (Windows).

Uso en Thonny:
  1. Archivo → Abrir → scripts/arrancar_workbench_thonny.py
  2. Run (F5)
  3. Se abre http://127.0.0.1:8765 → QL → Guided Lab
  4. Enter en la consola para apagar el servidor (solo si ESTE script lo inició)
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

REPO = Path(r"C:\Users\ssciarratta\Desktop\QuantLab")
URL = "http://127.0.0.1:8765"
PORT = 8765


def load_dotenv(path: Path) -> None:
    """Carga .env simple (KEY=VALUE) al os.environ."""
    if not path.is_file():
        print("Aviso: no hay .env — Guided Lab paper funciona igual.")
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
    print("OK: .env cargado (secrets no se imprimen).")


def server_alive(url: str = URL, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def workbench_cmd() -> list[str]:
    """Preferir .venv directo (evita uv sync y el lock del .exe en Windows)."""
    exe = REPO / ".venv" / "Scripts" / "quantlab-workbench.exe"
    if exe.is_file():
        return [str(exe), "--no-browser", "--port", str(PORT)]
    py = REPO / ".venv" / "Scripts" / "python.exe"
    if py.is_file():
        return [str(py), "-m", "quantlab.workbench.launch", "--no-browser", "--port", str(PORT)]
    return ["uv", "run", "quantlab-workbench", "--no-browser", "--port", str(PORT)]


def main() -> int:
    if not REPO.is_dir():
        print("ERROR: no existe la carpeta:", REPO)
        return 1

    os.chdir(REPO)
    load_dotenv(REPO / ".env")

    print("QuantLab Workbench")
    print("Repo:", REPO)
    print("URL:", URL)

    if server_alive():
        print("\n=== Ya está corriendo ===")
        print("Otro proceso (o una corrida anterior) ya usa el puerto", PORT)
        webbrowser.open(URL)
        print("Navegador abierto → QL → Guided Lab")
        print("\nPara apagar el servidor viejo: cerrá la terminal donde corre,")
        print("o en Git Bash: taskkill //F //PID <pid del python en :8765>")
        return 0

    cmd = workbench_cmd()
    print("Arrancando:", " ".join(cmd))

    proc = subprocess.Popen(cmd, cwd=str(REPO), shell=False)

    for _ in range(15):
        time.sleep(1)
        if proc.poll() is not None:
            print("ERROR: el workbench terminó (código", proc.returncode, ")")
            print("Si dice 'archivo en uso': hay otro workbench abierto.")
            print("Solución: cerrá terminales viejas o reiniciá PC.")
            print("Luego una sola vez: uv sync --extra dev")
            return proc.returncode or 1
        if server_alive():
            break
    else:
        print("ERROR: timeout esperando", URL)
        proc.terminate()
        return 1

    webbrowser.open(URL)
    print("\n=== Workbench corriendo ===")
    print("Menú: botón QL (abajo izq) → Guided Lab")
    print("Para apagar ESTE servidor: Enter acá abajo\n")

    try:
        input("Enter para detener el servidor… ")
    except KeyboardInterrupt:
        print("\nCtrl+C — apagando…")

    proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("Workbench detenido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
