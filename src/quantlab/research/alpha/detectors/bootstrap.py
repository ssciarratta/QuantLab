"""Import side-effect: registra detectores pairwise al cargar."""


def ensure_pairwise_detectors_loaded() -> None:
    from quantlab.research.alpha.detectors import (  # noqa: F401
        cointegration,
        contemporary_correlation,
        lagged_correlation,
        pair_spread,
    )
