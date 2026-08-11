"""Importa keys Futures Testnet desde Hummingbot (WSL) al .env de QuantLab.

Uso (desde raíz QuantLab, sin imprimir secretos):
  python scripts/import_hb_futures_keys_to_env.py

Requiere WSL + connector cifrado + password bootstrap (default: scalping).
No toca BINANCE_DEMO_* (Spot). Desactiva QUANTLAB_DEMO_USE_TESTNET.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _decrypt_from_wsl(password: str) -> tuple[str, str]:
    py = "/root/miniconda3/envs/hummingbot/bin/python"
    script = f"""
from eth_keyfile import decode_keyfile_json
from pathlib import Path
import json
pw={password!r}.encode()
yml=Path('/root/hummingbot/conf/connectors/binance_perpetual_testnet.yml').read_text()
out={{}}
for line in yml.splitlines():
    if line.startswith('binance_perpetual_testnet_api_'):
        k,v=line.split(':',1)
        obj=json.loads(bytes.fromhex(v.strip()).decode())
        out[k.strip()]=decode_keyfile_json(obj, pw).decode()
print(out['binance_perpetual_testnet_api_key'])
print(out['binance_perpetual_testnet_api_secret'])
"""
    proc = subprocess.run(
        ["wsl", "-e", "bash", "-lc", f"{py} - <<'PY'\n{script}\nPY"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"No se pudieron descifrar keys HB: {proc.stderr.strip()}")
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if len(lines) < 2:
        raise SystemExit("Salida HB inesperada (faltan key/secret).")
    return lines[0], lines[1]


def _upsert_env(path: Path, updates: dict[str, str]) -> None:
    existing: dict[str, str] = {}
    order: list[str] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            k, _, v = stripped.partition("=")
            k = k.strip()
            if k and k not in existing:
                order.append(k)
            existing[k] = v
    for k, v in updates.items():
        if k not in existing:
            order.append(k)
        existing[k] = v
    body = "\n".join(f"{k}={existing[k]}" for k in order) + "\n"
    path.write_text(body, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--password", default="scalping")
    parser.add_argument("--live-user", default="operator")
    parser.add_argument("--live-password", default="quantlab-local")
    args = parser.parse_args()
    key, secret = _decrypt_from_wsl(args.password)
    env_path = args.root / ".env"
    _upsert_env(
        env_path,
        {
            "QUANTLAB_LIVE_USER": args.live_user,
            "QUANTLAB_LIVE_PASSWORD": args.live_password,
            "QUANTLAB_DEMO_USE_FUTURES_TESTNET": "1",
            "BINANCE_FUTURES_DEMO_API_KEY": key,
            "BINANCE_FUTURES_DEMO_API_SECRET": secret,
            "QUANTLAB_DEMO_USE_TESTNET": "0",
        },
    )
    print(
        f"[OK] .env actualizado con Futures Testnet "
        f"(key_len={len(key)} secret_len={len(secret)}; valores no mostrados)."
    )
    print("Spot remoto=0. Unlock LIVE user=operator (cambiar si querés).")
    print("Siguiente: quantlab-testnet diagnostic --market futures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
