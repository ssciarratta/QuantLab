"""Estadísticos incrementales + histograma + reservoir (memoria acotada)."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WelfordAccumulator:
    """Media / varianza online (población, pstdev-compatible)."""

    n: int = 0
    mean: float = 0.0
    m2: float = 0.0
    min_v: float = float("inf")
    max_v: float = float("-inf")

    def add(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.m2 += delta * delta2
        if x < self.min_v:
            self.min_v = x
        if x > self.max_v:
            self.max_v = x

    @property
    def variance(self) -> float:
        if self.n < 1:
            return 0.0
        return self.m2 / self.n

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)


@dataclass
class OutcomeCounter:
    """Conteos vs capital inicial."""

    initial: float | None
    profit: int = 0
    loss: int = 0
    above: int = 0
    n: int = 0

    def add(self, final: float) -> None:
        self.n += 1
        if self.initial is None:
            return
        if final > self.initial:
            self.profit += 1
        elif final < self.initial:
            self.loss += 1
        if final >= self.initial:
            self.above += 1

    def probs(self) -> tuple[float | None, float | None, float | None]:
        if self.initial is None or self.n == 0:
            return None, None, None
        return self.profit / self.n, self.loss / self.n, self.above / self.n


@dataclass
class ReservoirSample:
    """Muestreo reproducible de equities finales."""

    capacity: int
    seed: int
    values: list[float] = field(default_factory=list)
    seen: int = 0
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed ^ 0xC0FFEE)

    def add(self, x: float) -> None:
        self.seen += 1
        if len(self.values) < self.capacity:
            self.values.append(x)
            return
        j = self._rng.randrange(self.seen)
        if j < self.capacity:
            self.values[j] = x


@dataclass
class IncrementalHistogram:
    """Histograma de ancho fijo; se reescala si aparecen extremos fuera de rango.

    Primera pasada usa rango expandible con bins fijos (rebin simple).
    """

    n_bins: int = 40
    counts: list[int] = field(default_factory=list)
    edges: list[float] = field(default_factory=list)
    _lo: float | None = None
    _hi: float | None = None
    _buffer: list[float] = field(default_factory=list)
    _buffer_max: int = 512

    def add(self, x: float) -> None:
        if self._lo is None:
            self._buffer.append(x)
            if len(self._buffer) >= self._buffer_max:
                self._init_from_buffer()
            return
        assert self._hi is not None
        if x < self._lo or x > self._hi:
            self._expand(x)
        self._count(x)

    def _init_from_buffer(self) -> None:
        if not self._buffer:
            return
        lo = min(self._buffer)
        hi = max(self._buffer)
        if hi <= lo:
            hi = lo + 1.0
        pad = (hi - lo) * 0.05 or 1.0
        self._lo = lo - pad
        self._hi = hi + pad
        self.edges = self._make_edges(self._lo, self._hi)
        self.counts = [0] * self.n_bins
        for v in self._buffer:
            self._count(v)
        self._buffer.clear()

    def _make_edges(self, lo: float, hi: float) -> list[float]:
        step = (hi - lo) / self.n_bins
        return [lo + i * step for i in range(self.n_bins + 1)]

    def _expand(self, x: float) -> None:
        assert self._lo is not None and self._hi is not None
        old_edges = list(self.edges)
        old_counts = list(self.counts)
        self._lo = min(self._lo, x)
        self._hi = max(self._hi, x)
        pad = (self._hi - self._lo) * 0.05 or 1.0
        self._lo -= pad
        self._hi += pad
        self.edges = self._make_edges(self._lo, self._hi)
        self.counts = [0] * self.n_bins
        # Rebin aproximado: centro de bin viejo
        for i, c in enumerate(old_counts):
            if c <= 0 or i >= len(old_edges) - 1:
                continue
            mid = 0.5 * (old_edges[i] + old_edges[i + 1])
            for _ in range(c):
                self._count(mid)

    def _count(self, x: float) -> None:
        if not self.edges:
            return
        if x <= self.edges[0]:
            self.counts[0] += 1
            return
        if x >= self.edges[-1]:
            self.counts[-1] += 1
            return
        # bin search lineal OK para 40 bins
        for i in range(self.n_bins):
            if self.edges[i] <= x < self.edges[i + 1]:
                self.counts[i] += 1
                return
        self.counts[-1] += 1

    def finalize(self) -> dict[str, Any]:
        if self._buffer:
            self._init_from_buffer()
        return {
            "bins": list(self.edges),
            "counts": list(self.counts),
            "n_bins": self.n_bins,
            "approximate": True,
        }


@dataclass
class IncrementalMonteCarloStats:
    """Agregador principal para corridas grandes."""

    initial_equity: float | None
    seed: int
    histogram_bins: int = 40
    reservoir_size: int = 2000
    keep_all: bool = True
    welford: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    outcomes: OutcomeCounter = field(init=False)
    reservoir: ReservoirSample = field(init=False)
    histogram: IncrementalHistogram = field(init=False)
    all_finals: list[float] = field(default_factory=list)
    failed: int = 0

    def __post_init__(self) -> None:
        self.outcomes = OutcomeCounter(initial=self.initial_equity)
        self.reservoir = ReservoirSample(capacity=self.reservoir_size, seed=self.seed)
        self.histogram = IncrementalHistogram(n_bins=self.histogram_bins)

    def add_equity(self, eq: float) -> None:
        self.welford.add(eq)
        self.outcomes.add(eq)
        self.histogram.add(eq)
        self.reservoir.add(eq)
        if self.keep_all:
            self.all_finals.append(eq)

    def add_failure(self) -> None:
        self.failed += 1

    def percentiles_from_sample(self) -> tuple[float | None, float | None, float | None]:
        """(p05, median, p95). Exactos si keep_all; aproximados vía reservoir si no."""
        src = sorted(self.all_finals if self.keep_all else self.reservoir.values)
        if not src:
            return None, None, None
        return (
            _percentile(src, 0.05),
            _percentile(src, 0.50),
            _percentile(src, 0.95),
        )

    def snapshot(self) -> dict[str, Any]:
        p05, med, p95 = self.percentiles_from_sample()
        pp, pl, pa = self.outcomes.probs()
        return {
            "n": self.welford.n,
            "failed": self.failed,
            "mean": self.welford.mean if self.welford.n else None,
            "std": self.welford.std if self.welford.n > 1 else 0.0,
            "min": self.welford.min_v if self.welford.n else None,
            "max": self.welford.max_v if self.welford.n else None,
            "median": med,
            "p05": p05,
            "p95": p95,
            "percentiles_approximate": not self.keep_all,
            "prob_profit": pp,
            "prob_loss": pl,
            "prob_above_initial": pa,
            "histogram": self.histogram.finalize(),
            "sample_final_equities": list(self.reservoir.values),
            "final_equities": list(self.all_finals) if self.keep_all else None,
        }


def _percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_vals[lo])
    w = pos - lo
    return float(sorted_vals[lo] * (1 - w) + sorted_vals[hi] * w)
