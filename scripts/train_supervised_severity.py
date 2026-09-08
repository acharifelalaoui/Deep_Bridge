#!/usr/bin/env python3
"""Entrainement supervise minimal sur annotations JSON."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ml.supervised import train_severity_classifier
from app.utils.paths import EXPORTS_DIR


def main() -> None:
    ann = EXPORTS_DIR / "annotations_demo.json"
    if not ann.exists():
        ann = EXPORTS_DIR / "annotations.json"
    if not ann.exists():
        print("Aucun fichier annotations.json trouve. Lance d'abord:")
        print("  python scripts/generate_demo_annotations.py")
        print("ou sauve des labels depuis l'interface.")
        return
    report = train_severity_classifier(ann)
    print(report.message)
    print(f"n={report.n_samples} classes={report.classes} acc={report.accuracy}")
    if report.model_path:
        print(f"modele: {report.model_path}")


if __name__ == "__main__":
    main()
