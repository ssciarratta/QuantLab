"""ReportGenerator HTML — contratos neutrales (Fase 8) + escalabilidad Bloque 3."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.results import MetricsResult, SimulationResult
from quantlab.data.atomic_io import atomic_write_text


@dataclass(frozen=True, slots=True)
class ReportResult:
    path: str
    template: str
    bytes_written: int


_DEFAULT_PRIMARY_METRICS: tuple[str, ...] = (
    "sharpe",
    "sortino",
    "calmar",
    "max_drawdown",
    "win_rate",
    "profit_factor",
    "total_return",
    "n_trades",
)

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
    h2 {{ font-size: 1rem; font-weight: 500; color: var(--muted); margin-top: 1.75rem; }}
    .metrics-wrap {{
      max-height: {metrics_max_height};
      overflow-y: auto;
      max-width: 720px;
      border: 1px solid #243041;
      border-radius: 4px;
    }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #243041; }}
    th {{
      color: var(--accent); font-weight: 500;
      position: sticky; top: 0; background: var(--bg);
    }}
    .chart {{
      margin-top: 2rem; height: 120px;
      display: flex; align-items: flex-end; gap: 2px;
      max-width: 100%; overflow-x: auto;
    }}
    .bar {{
      background: linear-gradient(180deg, var(--accent), #1a4a7a);
      width: 6px; min-height: 2px; flex: 0 0 auto;
    }}
    .note {{ color: var(--muted); font-size: 0.85rem; margin-top: 0.5rem; }}
  </style>
</head>
<body>
  <h1>QuantLab</h1>
  <p class="meta">Experimento {experiment_id} · metrics {metrics_version}</p>
  <h2>Métricas principales</h2>
  <div class="metrics-wrap">
    <table>
      <thead><tr><th>Métrica</th><th>Valor</th></tr></thead>
      <tbody>
{primary_rows}
      </tbody>
    </table>
  </div>
{secondary_block}
  <div class="chart" title="Equity curve (downsampled, normalizada)">
{bars}
  </div>
  <p class="note">{equity_note}</p>
</body>
</html>
"""


def downsample_equities(
    equities: Sequence[float],
    max_points: int = 100,
) -> list[float]:
    """Downsampling uniforme a lo largo de toda la curva (incluye inicio y fin)."""
    if max_points < 2:
        raise ValidationError("max_points debe ser >= 2")
    n = len(equities)
    if n == 0:
        return []
    if n <= max_points:
        return [float(x) for x in equities]
    out: list[float] = []
    last_idx = n - 1
    for i in range(max_points):
        idx = int(round(i * last_idx / (max_points - 1)))
        out.append(float(equities[idx]))
    out[0] = float(equities[0])
    out[-1] = float(equities[-1])
    return out


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
        max_equity_points: int = 100,
        primary_metrics: Sequence[str] | None = None,
        max_table_rows: int | None = None,
        metrics_max_height: str = "320px",
    ) -> ReportResult:
        if primary_metrics is not None:
            primary_keys = tuple(primary_metrics)
        else:
            primary_keys = _DEFAULT_PRIMARY_METRICS
        primary_rows, secondary_rows, truncated = _split_metric_rows(
            metrics.metrics,
            primary_keys=primary_keys,
            max_table_rows=max_table_rows,
        )
        secondary_block = ""
        if secondary_rows:
            secondary_block = (
                "  <h2>Métricas detalladas</h2>\n"
                '  <div class="metrics-wrap">\n'
                "    <table>\n"
                "      <thead><tr><th>Métrica</th><th>Valor</th></tr></thead>\n"
                "      <tbody>\n"
                f"{secondary_rows}\n"
                "      </tbody>\n"
                "    </table>\n"
                "  </div>\n"
            )
            if truncated > 0:
                secondary_block += (
                    f'  <p class="note">… {truncated} métricas adicionales omitidas '
                    f"(max_table_rows={max_table_rows})</p>\n"
                )

        bars_html = ""
        equity_note = "Sin curva de equidad."
        if simulation and simulation.equity_curve:
            eqs = [float(p.equity) for p in simulation.equity_curve]
            sampled = downsample_equities(eqs, max_points=max_equity_points)
            lo, hi = min(eqs), max(eqs)
            span = (hi - lo) or 1.0
            for eq in sampled:
                h = max(2, int(100 * (eq - lo) / span))
                bars_html += f'    <div class="bar" style="height:{h}px"></div>\n'
            equity_note = (
                f"Equity: {len(eqs)} puntos → {len(sampled)} mostrados "
                f"(downsample uniforme, max={max_equity_points})."
            )

        html = _TEMPLATE.format(
            experiment_id=escape(metrics.experiment_id),
            metrics_version=escape(metrics.metrics_version),
            primary_rows=primary_rows,
            secondary_block=secondary_block,
            bars=bars_html,
            equity_note=escape(equity_note),
            metrics_max_height=escape(metrics_max_height),
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


def _split_metric_rows(
    metrics: Mapping[str, Any],
    *,
    primary_keys: Sequence[str],
    max_table_rows: int | None,
) -> tuple[str, str, int]:
    """Devuelve (primary_html, secondary_html, truncated_count)."""
    primary_set = set(primary_keys)
    present_primary = [k for k in primary_keys if k in metrics]
    secondary = sorted(k for k in metrics if k not in primary_set)

    truncated = 0
    if max_table_rows is not None:
        if max_table_rows < 0:
            raise ValidationError("max_table_rows debe ser >= 0")
        # Cupo total: primarias tienen prioridad; el resto va a secundarias.
        primary_budget = min(len(present_primary), max_table_rows)
        present_primary = present_primary[:primary_budget]
        secondary_budget = max(0, max_table_rows - len(present_primary))
        if len(secondary) > secondary_budget:
            truncated = len(secondary) - secondary_budget
            secondary = secondary[:secondary_budget]

    primary_rows = "\n".join(_row_html(k, metrics[k]) for k in present_primary)
    secondary_rows = "\n".join(_row_html(k, metrics[k]) for k in secondary)
    return primary_rows, secondary_rows, truncated


def _row_html(key: str, val: Any) -> str:
    return f"      <tr><td>{escape(str(key))}</td><td>{escape(str(val))}</td></tr>"
