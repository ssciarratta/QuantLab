"""Detección read-only de Hummingbot (proceso externo, sin order routing)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _run_cmd(args: list[str], *, timeout: float = 5.0) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def _docker_hummingbot_running() -> bool:
    if shutil.which("docker") is None:
        return False
    code, out = _run_cmd(
        ["docker", "ps", "--format", "{{.Names}}"],
        timeout=8.0,
    )
    if code != 0:
        return False
    lowered = out.lower()
    return "hummingbot" in lowered or "hbot" in lowered


def _wsl_hummingbot_hint() -> bool:
    if shutil.which("wsl") is None:
        return False
    code, out = _run_cmd(["wsl", "-e", "bash", "-lc", "command -v hummingbot"], timeout=10.0)
    return code == 0 and bool(out.strip())


def _native_hummingbot_hint() -> bool:
    return shutil.which("hummingbot") is not None or shutil.which("hbot") is not None


def _conf_paths() -> list[Path]:
    home = Path.home()
    candidates = [
        home / "hummingbot" / "conf",
        home / "hummingbot_files" / "conf",
        Path("conf"),
        Path("hummingbot") / "conf",
    ]
    env_conf = os.environ.get("HUMMINGBOT_CONF_DIR", "").strip()
    if env_conf:
        candidates.insert(0, Path(env_conf))
    return [p for p in candidates if p.is_dir()]


def _scan_conf_for_production_markers(conf_dir: Path) -> dict[str, Any]:
    """Busca referencias a producción en configs locales (read-only)."""
    findings: list[str] = []
    safe_testnet_markers = ("binance_paper_trade", "binance_perpetual_testnet", "testnet")
    prod_markers = ("api.binance.com", '"binance"', "connector: binance\n")
    for path in conf_dir.rglob("*.yml"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        if "api.binance.com" in text:
            findings.append(f"Posible producción en {path.name}: api.binance.com")
        if "connector_name: binance" in text.replace(" ", "") and "paper" not in text:
            findings.append(f"Posible connector spot mainnet en {path.name}")
        if any(marker in text for marker in safe_testnet_markers):
            findings.append(f"Marcador testnet/paper en {path.name}")
    return {"conf_dir": str(conf_dir.resolve()), "findings": findings}


def hummingbot_status() -> dict[str, Any]:
    """Estado Hummingbot sin invocar trading ni exponer secrets."""
    detection_method = "none"
    installed = False
    if _docker_hummingbot_running():
        installed = True
        detection_method = "docker"
    elif _native_hummingbot_hint():
        installed = True
        detection_method = "native_cli"
    elif _wsl_hummingbot_hint():
        installed = True
        detection_method = "wsl"

    conf_dirs = _conf_paths()
    conf_scan: list[dict[str, Any]] = []
    for conf_dir in conf_dirs[:3]:
        conf_scan.append(_scan_conf_for_production_markers(conf_dir))

    # Hummingbot no expone connector binance_testnet para spot (2026).
    recommendation = (
        "HB spot: usar binance_paper_trade (paper) o QuantLab F102 testnet nativo. "
        "Perp testnet: binance_perpetual_testnet. Mantener desacoplado vía exports."
    )
    return {
        "installed": installed,
        "detection_method": detection_method,
        "spot_testnet_connector_available": False,
        "recommended_spot_paper_connector": "binance_paper_trade",
        "recommended_perp_testnet_connector": "binance_perpetual_testnet",
        "conf_dirs_found": [str(p.resolve()) for p in conf_dirs],
        "conf_scan": conf_scan,
        "recommendation": recommendation,
        "quantlab_export_only": True,
        "note": (
            "QuantLab exporta JSON research-safe; Hummingbot corre como proceso externo."
        ),
    }


def verify_hummingbot_testnet_safety() -> dict[str, Any]:
    """Verificación de seguridad: no debe apuntar a producción spot."""
    status = hummingbot_status()
    issues: list[str] = []
    for scan in status.get("conf_scan") or []:
        for finding in scan.get("findings") or []:
            lower = finding.lower()
            if "api.binance.com" in lower or "mainnet" in lower:
                issues.append(finding)
    ok = not issues
    return {
        "ok": ok,
        "installed": status.get("installed"),
        "issues": issues,
        "status": status,
    }
