"""Feature Pipeline composable — orquestador causal (Fase 5 Oficial M2)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from quantlab.core.exceptions import ValidationError
from quantlab.core.types.market import Bar
from quantlab.core.types.validation import require_non_empty_str
from quantlab.features.causal import assert_bars_causal_ready
from quantlab.features.contracts import (
    FEATURES_SCHEMA_VERSION,
    FeatureFrame,
    FeatureSeries,
    FeatureTransformer,
)


@dataclass(frozen=True, slots=True)
class FeaturePipeline:
    """Encadena transformers y produce un FeatureFrame inmutable.

    Procesamiento "vectorial": cada step transforma la serie completa de barras
    de una sola pasada. La validación causal se ejecuta una sola vez en `run`.
    """

    steps: tuple[FeatureTransformer, ...]
    name: str = "feature_pipeline"

    def __post_init__(self) -> None:
        require_non_empty_str(self.name, "name")
        if not self.steps:
            raise ValidationError("pipeline requiere al menos un transformer")
        names = [s.name for s in self.steps]
        if len(names) != len(set(names)):
            raise ValidationError("nombres de transformers duplicados en el pipeline")

    @property
    def min_lookback(self) -> int:
        return max(step.min_lookback for step in self.steps)

    def then(self, step: FeatureTransformer) -> FeaturePipeline:
        """Devuelve un pipeline nuevo con un step adicional (composición inmutable)."""
        return FeaturePipeline(steps=(*self.steps, step), name=self.name)

    def run(self, bars: Sequence[Bar]) -> FeatureFrame:
        assert_bars_causal_ready(bars, min_lookback=self.min_lookback)
        series_map: dict[str, FeatureSeries] = {}
        for step in self.steps:
            series = step.transform(bars, skip_causal_check=True)
            if series.name in series_map:
                raise ValidationError(f"serie duplicada: {series.name}")
            series_map[series.name] = series
        return FeatureFrame(
            instrument_id=bars[0].instrument_id,
            schema_version=FEATURES_SCHEMA_VERSION,
            series=series_map,
            min_lookback=self.min_lookback,
            bar_count=len(bars),
            pipeline_name=self.name,
        )

    def run_universe(
        self, bars_by_instrument: Mapping[str, Sequence[Bar]]
    ) -> dict[str, FeatureFrame]:
        """Ejecuta el pipeline sobre un universo multi-instrumento."""
        if not bars_by_instrument:
            raise ValidationError("universo vacío")
        out: dict[str, FeatureFrame] = {}
        for instrument_id, bars in bars_by_instrument.items():
            if not bars:
                raise ValidationError(f"sin barras para instrumento: {instrument_id}")
            if bars[0].instrument_id != instrument_id:
                raise ValidationError(
                    f"clave {instrument_id!r} no coincide con bars[0].instrument_id="
                    f"{bars[0].instrument_id!r}"
                )
            out[instrument_id] = self.run(bars)
        return out


def build_pipeline(
    *steps: FeatureTransformer,
    name: str = "feature_pipeline",
) -> FeaturePipeline:
    """Factory conveniente para armar un pipeline."""
    return FeaturePipeline(steps=tuple(steps), name=name)
