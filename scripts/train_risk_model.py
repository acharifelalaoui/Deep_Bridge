#!/usr/bin/env python3
"""Entrainement du modele de risque sur le CSV du groupe precedent."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ml.clinical_dataset import dataset_summary
from app.ml.risk_model import DEFAULT_MODEL_PATH, train_risk_model


def main() -> None:
    print(dataset_summary())
    _, metrics = train_risk_model()
    print("Modele sauvegarde:", DEFAULT_MODEL_PATH)
    print(
        f"n={metrics.n_samples} acc={metrics.accuracy:.3f} "
        f"precision={metrics.precision:.3f} recall={metrics.recall:.3f} "
        f"f1={metrics.f1:.3f} roc_auc={metrics.roc_auc:.3f}"
    )


if __name__ == "__main__":
    main()
