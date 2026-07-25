"""ReportGenerator HTML — contratos neutrales (Fase 8)."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

from quantlab.core.types.results import MetricsResult, SimulationResult
from quantlab.data.atomic_io import atomic_write_text


@dataclass(frozen=True, slots=True)
class ReportResult:
    path: str
    template: str
    bytes_written: int


_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>QuantLab Report — {experiment_id}</title>
  <style>
    :root {{ --bg:#0f1419; --fg:#e7ecf1; --accent:#3d9cf0; --muted:#8b9aab; }}
    body {{ font-family: "Segoe UI", sans-serif; background: var(--bg); color: var(--fg);
           margin: 0; padding: 2rem; }}
    h1 {{ font-weight: 600; letter-spacing: -0.02em; }}
    .meta {{ color: var(--muted); margin-bottom: 1.5rem; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 720px; }}
    th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #243041; }}
    th {{ color: var(--accent); font-weight: 500; }}
    .chart {{ margin-top: 2rem; height: 120px; display: flex; align-items: flex-end; gap: 2px; }}
    .bar {{
      background: linear-gradient(180deg, var(--accent), #1a4a7a);
      width: 6px; min-height: 2px;
    }}
  </style>
</head>
<body>
  <h1>QuantLab</h1>
  <p class="meta">Experimento {experiment_id} · metrics {metrics_version}</p>
  <table>
    <thead><tr><th>Métrica</th><th>Valor</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
  <div class="chart" title="Equity curve (normalizada)">
{bars}
  </div>
</body>
</html>
"""


class ReportGenerator:
    """Genera HTML desde MetricsResult + SimulationResult (sin importar engines)."""

    def __init__(self, output_dir: Path) -> None:
        self._root = output_dir
        self._root.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        *,
        metrics: MetricsResult,
        simulation: SimulationResult | None = None,
        template: str = "default_v1",
    ) -> ReportResult:
        rows = []
        for key in sorted(metrics.metrics.keys()):
            val = metrics.metrics[key]
            rows.append(
                f"      <tr><td>{escape(str(key))}</td><td>{escape(str(val))}</td></tr>"
            )
        bars_html = ""
        if simulation and simulation.equity_curve:
            eqs = [float(p.equity) for p in simulation.equity_curve]
            lo, hi = min(eqs), max(eqs)
            span = (hi - lo) or 1.0
            for eq in eqs[-80:]:
                h = max(2, int(100 * (eq - lo) / span))
                bars_html += f'    <div class="bar" style="height:{h}px"></div>\n'
        html = _TEMPLATE.format(
            experiment_id=escape(metrics.experiment_id),
            metrics_version=escape(metrics.metrics_version),
            rows="\n".join(rows),
            bars=bars_html,
        )
        path = self._root / metrics.experiment_id / f"report_{template}.html"
        atomic_write_text(path, html)
        return ReportResult(path=str(path), template=template, bytes_written=len(html.encode()))

    def list_templates(self) -> tuple[str, ...]:
        return ("default_v1",)

    def compare(self, left: MetricsResult, right: MetricsResult) -> dict[str, Any]:
        keys = sorted(set(left.metrics) | set(right.metrics))
        out: dict[str, Any] = {}
        for k in keys:
            out[k] = {"left": left.metrics.get(k), "right": right.metrics.get(k)}
        return out
