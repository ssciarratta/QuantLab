#!/usr/bin/env python3
"""Bootstrap / train Alpha ML GBM (research only, LIVE_BLOCKED).

Ejemplos:
  uv run python scripts/alpha_ml_bootstrap.py --synthetic --activate
  uv run python scripts/alpha_ml_bootstrap.py --trials path/to/experiments --activate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train Alpha ML GBM ranking model")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments") / "alpha_ml",
        help="Directorio registry modelos",
    )
    parser.add_argument("--synthetic", action="store_true", help="Dataset sintético")
    parser.add_argument("--n", type=int, default=80, help="Filas sintéticas")
    parser.add_argument(
        "--trials",
        type=Path,
        default=None,
        help="experiments_dir con alpha_trials",
    )
    parser.add_argument("--activate", action="store_true", help="Marcar modelo como activo")
    parser.add_argument("--min-pos", type=int, default=8)
    args = parser.parse_args(argv)

    from quantlab.research.alpha.ml.dataset import (
        build_dataset_from_trials,
        make_synthetic_dataset,
    )
    from quantlab.research.alpha.ml.registry import MlModelRegistry
    from quantlab.research.alpha.ml.train import train_gbm
    from quantlab.research.alpha.validation.trial_ledger import TrialLedger
    from quantlab.research.alpha.validation.validate_candidate import default_trials_path

    if args.synthetic:
        ds = make_synthetic_dataset(n=args.n, n_pos=max(8, args.n // 4))
        print(f"synthetic dataset n={len(ds.labels)} pos={ds.n_pos()}")
    elif args.trials is not None:
        path = default_trials_path(args.trials)
        led = TrialLedger(path=path)
        ds = build_dataset_from_trials(led, min_rows=args.min_pos)
        print(f"trials dataset n={len(ds.labels)} pos={ds.n_pos()} path={path}")
    else:
        print("Indicá --synthetic o --trials DIR", file=sys.stderr)
        return 2

    result = train_gbm(ds, out_dir=args.out, min_pos=args.min_pos, min_rows=args.min_pos + 5)
    print(
        f"trained model_id={result.model_id} backend={result.backend} "
        f"auc={result.metrics.get('auc')}"
    )
    print(f"path={result.path}")
    if args.activate:
        reg = MlModelRegistry(args.out)
        reg.set_active(result.model_id)
        print(f"active_model_id={result.model_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
